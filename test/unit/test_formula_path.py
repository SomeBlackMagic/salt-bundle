import tarfile
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from salt_bundle.packaging.models import PackageMeta
from salt_bundle.packaging.archives import pack_formula


class TestTopLevelDirPackaging(unittest.TestCase):
    def test_pack_formula_from_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp) / "my-formula"
            source_dir = formula_dir / "formula"
            source_dir.mkdir(parents=True)

            (formula_dir / "FORMULA").write_text(
                "\n".join([
                    "name: my-formula",
                    "version: 1.0.0",
                    "top_level_dir: formula",
                    "dependencies: []",
                ]),
                encoding="utf-8",
            )
            (formula_dir / ".saltbundleignore").write_text("tests/**\n", encoding="utf-8")
            (formula_dir / "README.md").write_text("not packaged\n", encoding="utf-8")
            (source_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
            (source_dir / "config.sls").write_text("test: true\n", encoding="utf-8")
            (source_dir / "tests").mkdir()
            (source_dir / "tests" / "ignored.sls").write_text("ignored\n", encoding="utf-8")
            (source_dir / "_modules").mkdir()
            (source_dir / "_modules" / "mymod.py").write_text("# module\n", encoding="utf-8")

            archive_path = pack_formula(formula_dir)

            with tarfile.open(archive_path, "r:gz") as tar:
                names = sorted(tar.getnames())

            self.assertEqual(
                names,
                [
                    "FORMULA",
                    "_modules/mymod.py",
                    "config.sls",
                    "init.sls",
                ],
            )

    def test_pack_formula_uses_root_metadata_when_source_contains_formula(self):
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp) / "my-formula"
            source_dir = formula_dir / "formula"
            source_dir.mkdir(parents=True)

            (formula_dir / "FORMULA").write_text(
                "\n".join([
                    "name: my-formula",
                    "version: 1.0.0",
                    "top_level_dir: formula",
                    "description: root metadata",
                ]),
                encoding="utf-8",
            )
            (source_dir / "FORMULA").write_text(
                "\n".join([
                    "name: wrong",
                    "version: 9.9.9",
                    "description: source metadata",
                ]),
                encoding="utf-8",
            )
            (source_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            archive_path = pack_formula(formula_dir)

            with tarfile.open(archive_path, "r:gz") as tar:
                names = tar.getnames()
                metadata = tar.extractfile("FORMULA").read().decode("utf-8")

            self.assertEqual(names.count("FORMULA"), 1)
            self.assertIn("description: root metadata", metadata)
            self.assertNotIn("description: source metadata", metadata)

    def test_top_level_dir_validation_rejects_absolute_and_parent_paths(self):
        with self.assertRaises(ValidationError):
            PackageMeta(name="test", version="1.0.0", top_level_dir="/tmp/formula")

        with self.assertRaises(ValidationError):
            PackageMeta(name="test", version="1.0.0", top_level_dir="../formula")

    def test_empty_top_level_dir_is_absent(self):
        self.assertIsNone(PackageMeta(name="test", version="1.0.0", top_level_dir="").top_level_dir)
        self.assertIsNone(PackageMeta(name="test", version="1.0.0", top_level_dir=".").top_level_dir)


if __name__ == "__main__":
    unittest.main()
