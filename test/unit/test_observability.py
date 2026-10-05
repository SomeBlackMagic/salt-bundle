"""Observable logging contracts for target-aware runtime activation."""

import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from salt_bundle.activation.cache import RuntimeCache
from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest
from salt_bundle.activation.models import PackageName
from salt_bundle.activation.parser import parse_top_bundle
from salt_bundle.activation.resolver import ActivationResolver
from salt_bundle.dependencies.lock_models import LockFile, LockedDependency
from salt_bundle.dependencies.saltfile_models import RuntimeConfig
from salt_bundle.runtime.backends.base import ExecutionResult, RuntimeContext, SaltCommand
from salt_bundle.runtime.backends.minion import MinionRuntimeBackend
from salt_bundle.runtime.grouping import group_targets_by_runtime
from salt_bundle.salt import bundlefs, loader


class TestTargetAwareRuntimeObservability(unittest.TestCase):
    """Specify safe debug diagnostics for target-aware runtime operations."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.vendor_root = self.project_dir / "vendor"
        self.package_path = self.vendor_root / "acme" / "nginx"
        self.package_path.mkdir(parents=True)
        self.lock_data = LockFile(
            dependencies={
                "acme/nginx": LockedDependency(
                    version="1.2.0",
                    repository="default",
                    url="nginx.tar.gz",
                    digest="sha256:nginx",
                )
            }
        )
        loader._get_manifest_dirs.cache_clear()
        loader._logged_namespaces.clear()
        bundlefs.__opts__ = {}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _manifest(self, *, absolute_path: bool = False) -> RuntimeManifest:
        return RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint="a" * 64,
            packages=(
                ManifestPackageEntry(
                    name=PackageName.parse("acme/nginx"),
                    version="1.2.0",
                    package_type="formula",
                    digest="sha256:nginx",
                    path=(
                        str(self.package_path)
                        if absolute_path
                        else "vendor/acme/nginx"
                    ),
                ),
            ),
        )

    def _context(self) -> RuntimeContext:
        return RuntimeContext(
            project_root=self.project_dir,
            vendor_root=self.vendor_root,
            cache_dir=self.project_dir / ".salt-bundle",
            config=RuntimeConfig(),
        )

    def test_activation_logs_target_fingerprint_packages_and_resolution_duration_without_pillar_secrets(self) -> None:
        resolver = ActivationResolver(
            top_bundle=parse_top_bundle("base:\n  'web-*':\n    - acme/nginx\n"),
            lock_data=self.lock_data,
            vendor_root=self.vendor_root,
        )

        with self.assertLogs("salt_bundle.activation.resolver", logging.DEBUG) as logs:
            resolver.resolve(
                "web-01",
                pillar={"database_password": "do-not-log-this-secret"},
            )

        output = "\n".join(logs.output)
        self.assertIn("target=web-01", output)
        self.assertIn("fingerprint=", output)
        self.assertIn("packages=[acme/nginx]", output)
        self.assertIn("resolution_duration_ms=", output)
        self.assertNotIn("do-not-log-this-secret", output)

    def test_loader_logs_target_namespace_and_active_paths(self) -> None:
        modules = self.package_path / "_modules"
        modules.mkdir()
        manifest = self._manifest(absolute_path=True)

        with self.assertLogs("salt_bundle.salt.loader", logging.DEBUG) as logs:
            result = loader.module_dirs(
                {"id": "web-01", "salt_bundle_runtime_manifest": manifest}
            )

        output = "\n".join(logs.output)
        self.assertEqual(result, [str(modules)])
        self.assertIn("target=web-01", output)
        self.assertIn("namespace=modules", output)
        self.assertIn(str(modules), output)

    def test_bundlefs_logs_target_and_active_roots(self) -> None:
        manifest = self._manifest(absolute_path=True)
        opts = {"id": "web-01", "salt_bundle_runtime_manifest": manifest}

        with patch.object(bundlefs, "__opts__", opts), self.assertLogs(
            "salt_bundle.salt.bundlefs", logging.DEBUG
        ) as logs:
            roots = bundlefs._get_active_roots()

        output = "\n".join(logs.output)
        self.assertEqual(roots, [(self.package_path, "formula")])
        self.assertIn("target=web-01", output)
        self.assertIn(str(self.package_path), output)

    def test_runtime_cache_logs_manifest_miss_and_hit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = RuntimeCache(Path(directory))
            manifest = self._manifest()

            with self.assertLogs("salt_bundle.activation.cache", logging.DEBUG) as logs:
                self.assertIsNone(cache.get_manifest(manifest.fingerprint))
                cache.put_manifest(manifest)
                self.assertEqual(cache.get_manifest(manifest.fingerprint), manifest)

        output = "\n".join(logs.output)
        self.assertIn("cache=miss", output)
        self.assertIn("cache=hit", output)
        self.assertIn(f"fingerprint={manifest.fingerprint}", output)

    def test_grouping_logs_the_number_of_runtime_groups(self) -> None:
        resolver = Mock()
        active_set = Mock(target="web-01", saltenv="base")
        active_set.fingerprint = "shared-fingerprint"
        active_set.packages = ()
        resolver.resolve.return_value = active_set

        with self.assertLogs("salt_bundle.runtime.grouping", logging.DEBUG) as logs:
            groups = group_targets_by_runtime(["web-01", "web-02"], resolver)

        self.assertEqual(len(groups), 1)
        self.assertIn("runtime_groups=1", "\n".join(logs.output))

    def test_minion_backend_logs_preparation_and_execution_durations(self) -> None:
        command_executor = Mock(
            return_value=[
                ExecutionResult(
                    target="web-01", success=True, return_data=True, retcode=0
                )
            ]
        )
        backend = MinionRuntimeBackend(command_executor)
        manifest = self._manifest()

        with self.assertLogs("salt_bundle.runtime.backends.minion", logging.DEBUG) as logs:
            prepared = backend.prepare(["web-01"], manifest, self._context())
            results = backend.execute(
                prepared, SaltCommand(function="test.version", args=[], kwargs={})
            )

        output = "\n".join(logs.output)
        self.assertEqual(results[0].target, "web-01")
        self.assertIn("runtime_preparation_duration_ms=", output)
        self.assertIn("execution_duration_ms=", output)
        self.assertIn(f"fingerprint={manifest.fingerprint}", output)
