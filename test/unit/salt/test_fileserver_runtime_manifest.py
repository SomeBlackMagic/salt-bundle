"""Tests for manifest-aware bundlefs package selection."""

from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest
from salt_bundle.activation.models import PackageName
from salt_bundle.salt import fileserver


class TestManifestAwareBundlefs(unittest.TestCase):
    """Specify bundlefs behaviour for an activated package set."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.active_formula = self.project_dir / "vendor" / "acme" / "nginx"
        self.inactive_formula = self.project_dir / "vendor" / "contoso" / "apache"
        self.extension = self.project_dir / "vendor" / "community" / "systemd-helper"

        (self.active_formula / "nginx").mkdir(parents=True)
        (self.active_formula / "nginx" / "init.sls").write_text("nginx: {}\n")
        (self.active_formula / "_modules").mkdir()
        (self.active_formula / "_modules" / "nginx.py").write_text("def present(): pass\n")

        (self.inactive_formula / "apache").mkdir(parents=True)
        (self.inactive_formula / "apache" / "init.sls").write_text("apache: {}\n")
        (self.inactive_formula / "_modules").mkdir()
        (self.inactive_formula / "_modules" / "apache.py").write_text("def present(): pass\n")

        self.extension_modules = (
            self.extension / "src" / "saltext" / "systemd_helper" / "modules"
        )
        self.extension_modules.mkdir(parents=True)
        (self.extension_modules / "systemd.py").write_text("def present(): pass\n")
        (self.extension / "unexpected.sls").write_text("unexpected: {}\n")

        fileserver._CACHE.update(config_path=None, vendor_roots=None)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _manifest(self) -> RuntimeManifest:
        return RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint="active-runtime",
            packages=(
                ManifestPackageEntry(
                    name=PackageName.parse("acme/nginx"),
                    version="1.0.0",
                    package_type="formula",
                    digest="sha256:nginx",
                    path=str(self.active_formula),
                ),
                ManifestPackageEntry(
                    name=PackageName.parse("community/systemd-helper"),
                    version="1.0.0",
                    package_type="extension",
                    digest="sha256:systemd-helper",
                    path=str(self.extension),
                ),
            ),
        )

    def _opts(self) -> dict[str, RuntimeManifest]:
        return {"salt_bundle_runtime_manifest": self._manifest()}

    def test_find_file_serves_formula_state_from_an_active_package_only(self) -> None:
        fileserver.__opts__ = self._opts()

        found = fileserver.find_file("nginx/init.sls")

        self.assertEqual(found["path"], str(self.active_formula / "nginx" / "init.sls"))
        self.assertEqual(fileserver.find_file("apache/init.sls"), {"path": "", "rel": ""})

    def test_find_file_resolves_module_sync_paths_for_formula_and_extension(self) -> None:
        fileserver.__opts__ = self._opts()

        formula_module = fileserver.find_file("_modules/nginx.py")
        extension_module = fileserver.find_file("_modules/systemd.py")

        self.assertEqual(formula_module["path"], str(self.active_formula / "_modules" / "nginx.py"))
        self.assertEqual(extension_module["path"], str(self.extension_modules / "systemd.py"))
        self.assertEqual(fileserver.find_file("_modules/apache.py"), {"path": "", "rel": ""})

    def test_file_and_directory_lists_include_only_active_formula_and_extension_content(self) -> None:
        fileserver.__opts__ = self._opts()

        self.assertEqual(
            fileserver.file_list({}),
            ["_modules/nginx.py", "_modules/systemd.py", "nginx/init.sls"],
        )
        self.assertEqual(fileserver.dir_list({}), ["_modules", "nginx"])
        self.assertNotIn("systemd-helper/unexpected.sls", fileserver.file_list({}))
