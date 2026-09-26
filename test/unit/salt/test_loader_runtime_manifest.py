"""Tests for manifest-aware Salt loader directory callbacks."""

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest
from salt_bundle.activation.models import PackageName
from salt_bundle.salt import loader


class TestManifestAwareLoader(unittest.TestCase):
    """Specify target-aware loader directory selection."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.active_package = self.project_dir / "vendor" / "acme-nginx"
        self.inactive_package = self.project_dir / "vendor" / "contoso-nginx"
        loader._get_module_dirs.cache_clear()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _manifest(self, fingerprint: str, *packages: Path) -> RuntimeManifest:
        return RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint=fingerprint,
            packages=tuple(
                ManifestPackageEntry(
                    name=PackageName.parse(f"example/{package.name}"),
                    version="1.0.0",
                    package_type="formula",
                    digest=f"sha256:{package.name}",
                    path=str(package),
                )
                for package in packages
            ),
        )

    def test_module_dirs_returns_only_directories_from_active_packages(self) -> None:
        active_modules = self.active_package / "_modules"
        inactive_modules = self.inactive_package / "_modules"
        active_modules.mkdir(parents=True)
        inactive_modules.mkdir(parents=True)
        manifest = self._manifest("active-fingerprint", self.active_package)
        runtime_context = SimpleNamespace(get_manifest=Mock(return_value=manifest))

        with patch.object(loader, "runtime_context", runtime_context, create=True):
            result = loader.module_dirs({"id": "web-01"})

        self.assertEqual(result, [str(active_modules)])
        self.assertNotIn(str(inactive_modules), result)
        runtime_context.get_manifest.assert_called_once_with({"id": "web-01"})

    def test_module_dirs_uses_manifest_supplied_in_salt_options(self) -> None:
        active_modules = self.active_package / "_modules"
        active_modules.mkdir(parents=True)
        manifest = self._manifest("option-fingerprint", self.active_package)

        result = loader.module_dirs({"salt_bundle_runtime_manifest": manifest})

        self.assertEqual(result, [str(active_modules)])

    def test_loader_callbacks_return_an_empty_list_for_an_empty_manifest(self) -> None:
        manifest = self._manifest("empty-fingerprint")
        runtime_context = SimpleNamespace(get_manifest=Mock(return_value=manifest))

        with patch.object(loader, "runtime_context", runtime_context, create=True):
            self.assertEqual(loader.module_dirs({"id": "web-01"}), [])
            self.assertEqual(loader.states_dirs({"id": "web-01"}), [])

    def test_each_loader_namespace_uses_only_active_package_directories(self) -> None:
        namespace_callbacks = {
            "modules": "module_dirs",
            "auth": "auth_dirs",
            "states": "states_dirs",
            "cache": "cache_dirs",
            "executors": "executor_dirs",
            "grains": "grains_dirs",
            "log_handlers": "log_handlers_dirs",
            "matchers": "matchers_dirs",
            "metaproxy": "metaproxy_dirs",
            "netapi": "netapi_dirs",
            "pillar": "pillar_dirs",
            "queues": "queue_dirs",
            "returners": "returner_dirs",
            "roster": "roster_dirs",
            "runners": "runner_dirs",
            "sdb": "sdb_dirs",
            "serializers": "serializers_dirs",
            "output": "outputter_dirs",
            "pkgdb": "pkgdb_dirs",
            "pkgfiles": "pkgfiles_dirs",
            "tops": "top_dirs",
            "utils": "utils_dirs",
            "wrapper": "wrapper_dirs",
            "renderers": "render_dirs",
            "engines": "engines_dirs",
            "proxy": "proxy_dirs",
            "clouds": "cloud_dirs",
            "beacons": "beacons_dirs",
            "thorium": "thorium_dirs",
            "tokens": "tokens_dirs",
            "wheel": "wheel_dirs",
        }
        manifest = self._manifest("namespace-fingerprint", self.active_package)
        runtime_context = SimpleNamespace(get_manifest=Mock(return_value=manifest))

        for namespace in namespace_callbacks:
            (self.active_package / f"_{namespace}").mkdir(parents=True)
            (self.inactive_package / f"_{namespace}").mkdir(parents=True)

        with patch.object(loader, "runtime_context", runtime_context, create=True):
            for namespace, callback_name in namespace_callbacks.items():
                with self.subTest(namespace=namespace):
                    self.assertEqual(
                        getattr(loader, callback_name)({"id": "web-01"}),
                        [str(self.active_package / f"_{namespace}")],
                    )

    def test_loader_cache_keeps_directories_separate_for_each_manifest_fingerprint(self) -> None:
        active_modules = self.active_package / "_modules"
        replacement_modules = self.inactive_package / "_modules"
        active_modules.mkdir(parents=True)
        replacement_modules.mkdir(parents=True)
        first_manifest = self._manifest("first-fingerprint", self.active_package)
        second_manifest = self._manifest("second-fingerprint", self.inactive_package)
        runtime_context = SimpleNamespace(
            get_manifest=Mock(side_effect=(first_manifest, second_manifest))
        )

        with patch.object(loader, "runtime_context", runtime_context, create=True):
            first_result = loader.module_dirs({"id": "web-01"})
            second_result = loader.module_dirs({"id": "web-02"})

        self.assertEqual(first_result, [str(active_modules)])
        self.assertEqual(second_result, [str(replacement_modules)])

    def test_fileserver_dirs_includes_only_active_package_directories(self) -> None:
        active_fileserver = self.active_package / "_fileserver"
        inactive_fileserver = self.inactive_package / "_fileserver"
        active_fileserver.mkdir(parents=True)
        inactive_fileserver.mkdir(parents=True)
        manifest = self._manifest("fileserver-fingerprint", self.active_package)
        runtime_context = SimpleNamespace(get_manifest=Mock(return_value=manifest))

        with patch.object(loader, "runtime_context", runtime_context, create=True):
            result = loader.fileserver_dirs({"id": "web-01"})

        self.assertIn(str(active_fileserver), result)
        self.assertNotIn(str(inactive_fileserver), result)
