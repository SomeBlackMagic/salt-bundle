import tempfile
import unittest
from pathlib import Path

from salt_bundle.dependencies.index_models import Index, IndexEntry
from salt_bundle.storage.release import (
    PackageInfo,
    _is_valid_package_layout,
    discover_packages,
    is_new_version,
    release_packages,
)
from salt_bundle.storage.providers.local_provider import LocalReleaseProvider
from salt_bundle.packaging.models import PackageMeta


class TestReleaseExtended(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_is_new_version_no_index(self) -> None:
        meta = PackageMeta(name="example", version="1.0.0")
        info = PackageInfo(Path("."), meta)
        self.assertTrue(is_new_version(info, None))

    def test_is_new_version_not_in_index(self) -> None:
        meta = PackageMeta(name="example", version="1.0.0")
        info = PackageInfo(Path("."), meta)
        idx = Index(generated="2024-01-01T00:00:00", packages={})
        self.assertTrue(is_new_version(info, idx))

    def test_is_new_version_already_exists(self) -> None:
        meta = PackageMeta(name="example", version="1.0.0")
        info = PackageInfo(Path("."), meta)
        idx = Index(
            generated="2024-01-01T00:00:00",
            packages={"example": [IndexEntry(version="1.0.0", url="x", digest="sha256:x")]},
        )
        self.assertFalse(is_new_version(info, idx))

    def test_discover_packages_nonexistent_dir(self) -> None:
        with self.assertRaises(FileNotFoundError):
            discover_packages(self.root / "nonexistent")

    def test_discover_single_formula(self) -> None:
        formula_dir = self.root / "my-formula"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text("name: my-formula\nversion: 1.0.0\n", encoding="utf-8")
        (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        results = discover_packages(formula_dir, single_formula=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "my-formula")

    def test_discover_skips_invalid_name(self) -> None:
        formula_dir = self.root / "Bad Formula"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text("name: Bad Formula\nversion: 1.0.0\n", encoding="utf-8")
        (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        results = discover_packages(formula_dir, single_formula=True)
        self.assertEqual(results, [])

    def test_discover_skips_invalid_semver(self) -> None:
        formula_dir = self.root / "example"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text("name: example\nversion: bad\n", encoding="utf-8")
        (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        results = discover_packages(formula_dir, single_formula=True)
        self.assertEqual(results, [])

    def test_discover_extension_package(self) -> None:
        ext_dir = self.root / "my-ext"
        ext_dir.mkdir()
        (ext_dir / "EXTENSION").write_text("name: my-ext\nversion: 1.0.0\n", encoding="utf-8")
        mod_dir = ext_dir / "_modules"
        mod_dir.mkdir()
        (mod_dir / "mymod.py").write_text("", encoding="utf-8")

        results = discover_packages(ext_dir, single_formula=True)
        self.assertEqual(len(results), 1)

    def test_release_nonexistent_dir(self) -> None:
        provider = LocalReleaseProvider(self.root / "repo")
        with self.assertRaises(FileNotFoundError):
            release_packages(self.root / "nonexistent", provider)

    def test_is_valid_package_layout_formula(self) -> None:
        pkg_dir = self.root / "formula"
        pkg_dir.mkdir()
        (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        self.assertTrue(_is_valid_package_layout(pkg_dir, "formula"))

    def test_is_valid_package_layout_extension(self) -> None:
        pkg_dir = self.root / "ext"
        pkg_dir.mkdir()
        mod_dir = pkg_dir / "_modules"
        mod_dir.mkdir()
        self.assertTrue(_is_valid_package_layout(pkg_dir, "extension"))

    def test_is_valid_package_layout_invalid_extension(self) -> None:
        pkg_dir = self.root / "ext"
        pkg_dir.mkdir()
        (pkg_dir / "random_dir").mkdir()
        self.assertFalse(_is_valid_package_layout(pkg_dir, "extension"))

    def test_release_skip_packaging_missing_archive(self) -> None:
        formula_dir = self.root / "formulas" / "example"
        formula_dir.mkdir(parents=True)
        (formula_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        provider = LocalReleaseProvider(self.root / "repo")
        released, errors = release_packages(
            self.root / "formulas", provider, skip_packaging=True
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("Archive not found", errors[0])
