"""Tests for local activation of permanent Salt minions."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest, load_manifest
from salt_bundle.activation.models import PackageName
from salt_bundle.dependencies.saltfile_models import RuntimeConfig
from salt_bundle.salt import loader


class TestMinionRuntimeBackend(unittest.TestCase):
    """Specify manifest delivery and isolation for permanent minions."""

    @staticmethod
    def _backend_module():
        try:
            spec = importlib.util.find_spec("salt_bundle.runtime.backends.minion")
        except ModuleNotFoundError:
            return None
        if spec is None:
            return None

        from salt_bundle.runtime.backends import minion

        return minion

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.vendor_dir = self.project_dir / "vendor"
        self.cache_dir = self.project_dir / ".salt-bundle"
        loader._get_manifest_dirs.cache_clear()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _context(self):
        from salt_bundle.runtime.backends.base import RuntimeContext

        return RuntimeContext(
            project_root=self.project_dir,
            vendor_root=self.vendor_dir,
            cache_dir=self.cache_dir,
            config=RuntimeConfig(),
        )

    def _manifest(self, fingerprint: str, package_path: Path) -> RuntimeManifest:
        return RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint=fingerprint,
            packages=(
                ManifestPackageEntry(
                    name=PackageName.parse(f"example/{package_path.name}"),
                    version="1.0.0",
                    package_type="formula",
                    digest=f"sha256:{package_path.name}",
                    path=str(package_path.relative_to(self.project_dir)),
                ),
            ),
        )

    def test_prepare_delivers_manifest_to_its_fingerprint_runtime_directory(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "minion backend must provide local runtime activation",
        )
        manifest = self._manifest("runtime-a", self.vendor_dir / "acme" / "nginx")

        prepared = backend_module.MinionRuntimeBackend().prepare(
            ["server-01"], manifest, self._context()
        )

        expected_path = self.cache_dir / "runtimes" / "runtime-a" / "manifest.yaml"
        self.assertEqual(prepared.manifest, manifest)
        self.assertEqual(prepared.targets, ["server-01"])
        self.assertEqual(prepared.backend_state.manifest_path, expected_path)
        self.assertTrue(expected_path.is_file())
        self.assertEqual(load_manifest(expected_path), manifest)

    def test_prepared_minion_options_point_loader_to_delivered_manifest(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "minion backend must provide local runtime activation",
        )
        modules_dir = self.vendor_dir / "acme" / "nginx" / "_modules"
        modules_dir.mkdir(parents=True)
        manifest = self._manifest("runtime-loader", modules_dir.parent)

        prepared = backend_module.MinionRuntimeBackend().prepare(
            ["server-01"], manifest, self._context()
        )

        self.assertEqual(loader.module_dirs(prepared.backend_state.minion_opts), [str(modules_dir)])
        self.assertEqual(
            prepared.backend_state.minion_opts["salt_bundle_runtime_manifest_path"],
            str(prepared.backend_state.manifest_path),
        )

    def test_each_minion_runtime_exposes_only_its_own_package_modules(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "minion backend must provide local runtime activation",
        )
        nginx_modules = self.vendor_dir / "acme" / "nginx" / "_modules"
        apache_modules = self.vendor_dir / "contoso" / "apache" / "_modules"
        nginx_modules.mkdir(parents=True)
        apache_modules.mkdir(parents=True)
        backend = backend_module.MinionRuntimeBackend()

        nginx_runtime = backend.prepare(
            ["server-01"], self._manifest("runtime-nginx", nginx_modules.parent), self._context()
        )
        apache_runtime = backend.prepare(
            ["server-02"], self._manifest("runtime-apache", apache_modules.parent), self._context()
        )

        self.assertEqual(loader.module_dirs(nginx_runtime.backend_state.minion_opts), [str(nginx_modules)])
        self.assertEqual(loader.module_dirs(apache_runtime.backend_state.minion_opts), [str(apache_modules)])

    def test_same_module_name_in_separate_runtimes_does_not_mix_loader_paths(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "minion backend must provide local runtime activation",
        )
        first_modules = self.vendor_dir / "acme" / "nginx" / "_modules"
        second_modules = self.vendor_dir / "contoso" / "nginx" / "_modules"
        first_modules.mkdir(parents=True)
        second_modules.mkdir(parents=True)
        (first_modules / "nginx.py").write_text("SOURCE = 'acme'\n", encoding="utf-8")
        (second_modules / "nginx.py").write_text("SOURCE = 'contoso'\n", encoding="utf-8")
        backend = backend_module.MinionRuntimeBackend()

        first_runtime = backend.prepare(
            ["server-01"], self._manifest("runtime-acme", first_modules.parent), self._context()
        )
        second_runtime = backend.prepare(
            ["server-02"], self._manifest("runtime-contoso", second_modules.parent), self._context()
        )

        self.assertEqual(loader.module_dirs(first_runtime.backend_state.minion_opts), [str(first_modules)])
        self.assertEqual(loader.module_dirs(second_runtime.backend_state.minion_opts), [str(second_modules)])
