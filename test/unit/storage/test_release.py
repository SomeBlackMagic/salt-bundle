import tempfile
import unittest
from pathlib import Path

from salt_bundle.dependencies.index_models import Index
from salt_bundle.storage.providers.local_provider import LocalReleaseProvider
from salt_bundle.storage.release import discover_packages, release_packages
from salt_bundle.storage.vendor import (
    clear_vendor_dir,
    get_installed_packages,
    get_vendor_dir,
    is_package_installed,
)


class TestReleaseAndStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.packages_dir = self.root / "packages"
        self.package_dir = self.packages_dir / "example"
        self.package_dir.mkdir(parents=True)
        (self.package_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (self.package_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_discovers_and_releases_package_to_local_provider(self) -> None:
        provider = LocalReleaseProvider(self.root / "repository")

        discovered = discover_packages(self.packages_dir)
        self.assertEqual([(item.name, item.version) for item in discovered], [("example", "1.0.0")])

        released, errors = release_packages(self.packages_dir, provider)

        self.assertEqual(errors, [])
        self.assertEqual([(item.name, item.version) for item in released], [("example", "1.0.0")])
        index = provider.load_index()
        self.assertIsNotNone(index)
        self.assertIn("example", index.packages)
        self.assertTrue((self.root / "repository" / "example" / "example-1.0.0.tgz").exists())

    def test_dry_run_does_not_initialize_or_write_provider(self) -> None:
        provider = LocalReleaseProvider(self.root / "repository")

        released, errors = release_packages(self.package_dir, provider, dry_run=True, single_formula=True)

        self.assertEqual(errors, [])
        self.assertEqual(len(released), 1)
        self.assertFalse((self.root / "repository").exists())

    def test_vendor_helpers_detect_and_clear_installed_packages(self) -> None:
        vendor_dir = get_vendor_dir(self.root, "vendor")
        package_dir = vendor_dir / "example"
        package_dir.mkdir(parents=True)
        (package_dir / "EXTENSION").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (vendor_dir / "notes.txt").write_text("temporary", encoding="utf-8")

        self.assertTrue(is_package_installed("example", vendor_dir))
        self.assertEqual(get_installed_packages(vendor_dir), ["example"])
        clear_vendor_dir(vendor_dir)
        self.assertEqual(list(vendor_dir.iterdir()), [])

    def test_discovery_skips_invalid_and_release_skips_existing_version(self) -> None:
        invalid_dir = self.packages_dir / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "FORMULA").write_text("name: Invalid!\nversion: bad\n", encoding="utf-8")
        self.assertEqual(len(discover_packages(self.packages_dir)), 1)

        provider = LocalReleaseProvider(self.root / "repository")
        provider.initialize()
        provider.save_index(Index(generated="2024-01-01T00:00:00", packages={"example": []}))
        released, errors = release_packages(self.packages_dir, provider)
        self.assertEqual(len(released), 1)
        self.assertEqual(errors, [])
        released, errors = release_packages(self.packages_dir, provider)
        self.assertEqual(released, [])
        self.assertEqual(errors, [])
