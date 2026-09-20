import tempfile
import unittest
from pathlib import Path

from salt_bundle.packaging.archives import pack_formula
from salt_bundle.storage.vendor import (
    ensure_vendor_dir,
    get_installed_packages,
    install_package_to_vendor,
)


class TestVendorOperations(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_ensure_vendor_dir_creates_directory(self) -> None:
        vendor_dir = self.root / "vendor"
        self.assertFalse(vendor_dir.exists())
        ensure_vendor_dir(vendor_dir)
        self.assertTrue(vendor_dir.exists())

    def test_install_package_to_vendor_unpacks_archive(self) -> None:
        # Create a formula archive
        pkg_dir = self.root / "source"
        pkg_dir.mkdir()
        (pkg_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        archive = pack_formula(pkg_dir, self.root)

        vendor_dir = self.root / "vendor"
        vendor_dir.mkdir()
        result = install_package_to_vendor(archive, "example", vendor_dir)

        self.assertTrue((result / "FORMULA").exists())
        self.assertTrue((result / "init.sls").exists())

    def test_install_package_replaces_existing(self) -> None:
        pkg_dir = self.root / "source"
        pkg_dir.mkdir()
        (pkg_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        archive = pack_formula(pkg_dir, self.root)

        vendor_dir = self.root / "vendor"
        vendor_dir.mkdir()

        # Install once
        install_package_to_vendor(archive, "example", vendor_dir)
        # Install again (should replace)
        result = install_package_to_vendor(archive, "example", vendor_dir)
        self.assertTrue((result / "FORMULA").exists())

    def test_get_installed_packages_empty_dir(self) -> None:
        vendor_dir = self.root / "vendor"
        self.assertEqual(get_installed_packages(vendor_dir), [])
