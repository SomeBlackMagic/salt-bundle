"""Tests for manifest-aware bundlefs package selection."""

from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest
from salt_bundle.activation.models import PackageName
from salt_bundle.salt import bundlefs


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
        (self.active_formula / "FORMULA").write_text(
            "name: acme/nginx\nversion: 1.0.0\ntop_level_dir: states\n"
        )
        (self.active_formula / "states").mkdir()
        (self.active_formula / "states" / "init.sls").write_text("nginx: {}\n")
        (self.active_formula / "states" / "config.sls").write_text("nginx: {}\n")
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

        bundlefs._CACHE.update(config_path=None, vendor_roots=None)

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
        bundlefs.__opts__ = self._opts()

        found = bundlefs.find_file("acme/nginx/init.sls")

        self.assertEqual(found["path"], str(self.active_formula / "states" / "init.sls"))
        self.assertEqual(bundlefs.find_file("contoso/apache/init.sls"), {"path": "", "rel": ""})

    def test_find_file_resolves_module_sync_paths_for_formula_and_extension(self) -> None:
        bundlefs.__opts__ = self._opts()

        formula_module = bundlefs.find_file("_modules/nginx.py")
        extension_module = bundlefs.find_file("_modules/systemd.py")

        self.assertEqual(formula_module["path"], str(self.active_formula / "_modules" / "nginx.py"))
        self.assertEqual(extension_module["path"], str(self.extension_modules / "systemd.py"))
        self.assertEqual(bundlefs.find_file("_modules/apache.py"), {"path": "", "rel": ""})

    def test_top_level_dir_is_the_formula_state_root_but_not_the_loader_root(self) -> None:
        bundlefs.__opts__ = self._opts()

        found = bundlefs.find_file("acme/nginx/config.sls")

        self.assertEqual(found["path"], str(self.active_formula / "states" / "config.sls"))
        self.assertNotIn("states/config.sls", bundlefs.file_list({}))
        self.assertIn("acme/nginx/config.sls", bundlefs.file_list({}))
        self.assertEqual(
            bundlefs.find_file("_modules/nginx.py")["path"],
            str(self.active_formula / "_modules" / "nginx.py"),
        )

    def test_find_file_resolves_clouds_namespace_for_formula_and_extension(self) -> None:
        clouds_dir = self.active_formula / "_clouds"
        clouds_dir.mkdir()
        (clouds_dir / "mycloud.py").write_text("def avail_images(): pass\n")

        ext_clouds = self.extension / "src" / "saltext" / "systemd_helper" / "clouds"
        ext_clouds.mkdir(parents=True)
        (ext_clouds / "extcloud.py").write_text("def avail_sizes(): pass\n")

        bundlefs.__opts__ = self._opts()

        formula_cloud = bundlefs.find_file("_clouds/mycloud.py")
        extension_cloud = bundlefs.find_file("_clouds/extcloud.py")

        self.assertEqual(formula_cloud["path"], str(clouds_dir / "mycloud.py"))
        self.assertEqual(extension_cloud["path"], str(ext_clouds / "extcloud.py"))

    def test_file_and_directory_lists_include_only_active_formula_and_extension_content(self) -> None:
        bundlefs.__opts__ = self._opts()

        self.assertEqual(
            bundlefs.file_list({}),
            [
                "_modules/nginx.py",
                "_modules/systemd.py",
                "acme/nginx/config.sls",
                "acme/nginx/init.sls",
            ],
        )
        self.assertEqual(bundlefs.dir_list({}), ["_modules", "acme/nginx"])
        self.assertNotIn("community/systemd-helper/unexpected.sls", bundlefs.file_list({}))
