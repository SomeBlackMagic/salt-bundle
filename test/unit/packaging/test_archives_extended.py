import tempfile
import unittest
from pathlib import Path

from salt_bundle.packaging.archives import (
    pack_formula,
    pack_extension,
    pack_package,
    unpack_package,
    validate_package_name,
    validate_semver,
)


class TestArchivesExtended(unittest.TestCase):
    def test_validate_package_name(self) -> None:
        self.assertTrue(validate_package_name("example"))
        self.assertTrue(validate_package_name("my-formula"))
        self.assertTrue(validate_package_name("my_formula"))
        self.assertFalse(validate_package_name("Bad Name"))
        self.assertFalse(validate_package_name(""))

    def test_validate_semver(self) -> None:
        self.assertTrue(validate_semver("1.0.0"))
        self.assertTrue(validate_semver("0.1.0-alpha"))
        self.assertFalse(validate_semver("bad"))
        self.assertFalse(validate_semver("1.0"))

    def test_pack_formula_invalid_name_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp)
            (formula_dir / "FORMULA").write_text("name: Bad Name\nversion: 1.0.0\n", encoding="utf-8")
            (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                pack_formula(formula_dir)

    def test_pack_formula_invalid_version_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp)
            (formula_dir / "FORMULA").write_text("name: example\nversion: bad\n", encoding="utf-8")
            (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                pack_formula(formula_dir)

    def test_pack_formula_no_sls_files_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp)
            (formula_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                pack_formula(formula_dir)

    def test_pack_extension_invalid_name_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ext_dir = Path(tmp)
            (ext_dir / "EXTENSION").write_text("name: Bad Name\nversion: 1.0.0\n", encoding="utf-8")
            (ext_dir / "_modules").mkdir()
            (ext_dir / "_modules" / "mod.py").write_text("", encoding="utf-8")

            with self.assertRaises(ValueError):
                pack_extension(ext_dir)

    def test_pack_extension_no_module_dirs_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ext_dir = Path(tmp)
            (ext_dir / "EXTENSION").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                pack_extension(ext_dir)

    def test_pack_package_dispatches_to_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ext_dir = Path(tmp)
            (ext_dir / "EXTENSION").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
            (ext_dir / "_modules").mkdir()
            (ext_dir / "_modules" / "mod.py").write_text("", encoding="utf-8")

            archive = pack_package(ext_dir)
            self.assertTrue(archive.exists())
            self.assertIn("example-1.0.0", archive.name)

    def test_unpack_package_nonexistent_archive_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                unpack_package(Path(tmp) / "missing.tgz", Path(tmp) / "out")

    def test_pack_formula_with_top_level_dir_nonexistent_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            formula_dir = Path(tmp) / "my-formula"
            formula_dir.mkdir()
            (formula_dir / "FORMULA").write_text(
                "name: example\nversion: 1.0.0\ntop_level_dir: nonexistent\n",
                encoding="utf-8",
            )

            with self.assertRaises(FileNotFoundError):
                pack_formula(formula_dir)
