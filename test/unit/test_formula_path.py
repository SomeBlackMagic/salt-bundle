import tarfile
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from salt_bundle.models.package_models import PackageMeta
from salt_bundle.package import pack_formula


class TestFormulaPathPackaging(unittest.TestCase):
    def test_pack_formula_from_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp) / "my-formula"
            source_dir = formula_dir / "formula"
            source_dir.mkdir(parents=True)

            (formula_dir / ".saltbundle.yaml").write_text(
                "\n".join([
                    "name: my-formula",
                    "version: 1.0.0",
                    "formula_path: formula",
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
                    ".saltbundle.yaml",
                    "_modules/mymod.py",
                    "config.sls",
                    "init.sls",
                ],
            )

    def test_pack_formula_uses_root_metadata_when_source_contains_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp) / "my-formula"
            source_dir = formula_dir / "formula"
            source_dir.mkdir(parents=True)

            (formula_dir / ".saltbundle.yaml").write_text(
                "\n".join([
                    "name: my-formula",
                    "version: 1.0.0",
                    "formula_path: formula",
                    "description: root metadata",
                ]),
                encoding="utf-8",
            )
            (source_dir / ".saltbundle.yaml").write_text(
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
                metadata = tar.extractfile(".saltbundle.yaml").read().decode("utf-8")

            self.assertEqual(names.count(".saltbundle.yaml"), 1)
            self.assertIn("description: root metadata", metadata)
            self.assertNotIn("description: source metadata", metadata)

    def test_formula_path_validation_rejects_absolute_and_parent_paths(self):
        with self.assertRaises(ValidationError):
            PackageMeta(name="test", version="1.0.0", formula_path="/tmp/formula")

        with self.assertRaises(ValidationError):
            PackageMeta(name="test", version="1.0.0", formula_path="../formula")

    def test_empty_formula_path_is_absent(self):
        self.assertIsNone(PackageMeta(name="test", version="1.0.0", formula_path="").formula_path)
        self.assertIsNone(PackageMeta(name="test", version="1.0.0", formula_path=".").formula_path)


if __name__ == "__main__":
    unittest.main()
