"""Tests for runtime-specific Salt SSH Thin delivery."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest
from salt_bundle.activation.models import PackageName
from salt_bundle.dependencies.saltfile_models import RuntimeConfig
from salt_bundle.runtime.backends.base import ExecutionResult, SaltCommand


class TestSaltSSHRuntimeBackend(unittest.TestCase):
    """Specify isolated Thin payloads for Salt SSH execution groups."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.vendor_dir = self.project_dir / "vendor"
        self.cache_dir = self.project_dir / ".salt-bundle"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def _backend_module():
        try:
            spec = importlib.util.find_spec("salt_bundle.runtime.backends.salt_ssh")
        except ModuleNotFoundError:
            return None
        if spec is None:
            return None

        from salt_bundle.runtime.backends import salt_ssh

        return salt_ssh

    def _context(self):
        from salt_bundle.runtime.backends.base import RuntimeContext

        return RuntimeContext(
            project_root=self.project_dir,
            vendor_root=self.vendor_dir,
            cache_dir=self.cache_dir,
            config=RuntimeConfig(),
        )

    def _manifest(self, fingerprint: str, *packages: tuple[str, str, str]) -> RuntimeManifest:
        return RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint=fingerprint,
            packages=tuple(
                ManifestPackageEntry(
                    name=PackageName.parse(name),
                    version="1.0.0",
                    package_type=package_type,
                    digest=f"sha256:{name}",
                    path=path,
                )
                for name, package_type, path in packages
            ),
        )

    def test_prepare_materializes_only_active_formula_modules_in_fingerprint_payload(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "Salt SSH backend must provide runtime-specific Thin delivery",
        )
        active_module = self.vendor_dir / "acme" / "nginx" / "_modules" / "nginx.py"
        inactive_module = self.vendor_dir / "contoso" / "apache" / "_modules" / "apache.py"
        active_module.parent.mkdir(parents=True)
        inactive_module.parent.mkdir(parents=True)
        active_module.write_text("SOURCE = 'nginx'\n", encoding="utf-8")
        inactive_module.write_text("SOURCE = 'apache'\n", encoding="utf-8")
        manifest = self._manifest(
            "formula-runtime",
            ("acme/nginx", "formula", "vendor/acme/nginx"),
        )

        prepared = backend_module.SaltSSHRuntimeBackend().prepare(
            ["ssh-a"], manifest, self._context()
        )

        payload_dir = self.cache_dir / "runtimes" / "formula-runtime" / "thin"
        self.assertEqual(prepared.manifest, manifest)
        self.assertEqual(prepared.targets, ["ssh-a"])
        self.assertEqual(prepared.backend_state.thin_dir, payload_dir)
        self.assertEqual(
            (payload_dir / "_modules" / "nginx.py").read_text(encoding="utf-8"),
            "SOURCE = 'nginx'\n",
        )
        self.assertFalse((payload_dir / "_modules" / "apache.py").exists())

    def test_prepare_materializes_extension_namespace_from_vendor_source(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "Salt SSH backend must provide runtime-specific Thin delivery",
        )
        module = (
            self.vendor_dir
            / "community"
            / "example"
            / "src"
            / "saltext"
            / "example"
            / "modules"
            / "example.py"
        )
        module.parent.mkdir(parents=True)
        module.write_text("SOURCE = 'extension'\n", encoding="utf-8")
        manifest = self._manifest(
            "extension-runtime",
            ("community/example", "extension", "vendor/community/example"),
        )

        prepared = backend_module.SaltSSHRuntimeBackend().prepare(
            ["ssh-a"], manifest, self._context()
        )

        self.assertEqual(
            (
                prepared.backend_state.thin_dir
                / "saltext"
                / "example"
                / "modules"
                / "example.py"
            ).read_text(encoding="utf-8"),
            "SOURCE = 'extension'\n",
        )

    def test_prepare_uses_one_cached_thin_payload_and_roster_per_fingerprint_group(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "Salt SSH backend must provide runtime-specific Thin delivery",
        )
        manifest = self._manifest("shared-runtime")
        backend = backend_module.SaltSSHRuntimeBackend()

        first = backend.prepare(["ssh-a", "ssh-b"], manifest, self._context())
        second = backend.prepare(["ssh-c"], manifest, self._context())

        expected_thin_dir = self.cache_dir / "runtimes" / "shared-runtime" / "thin"
        self.assertEqual(first.backend_state.thin_dir, expected_thin_dir)
        self.assertEqual(second.backend_state.thin_dir, expected_thin_dir)
        self.assertEqual(first.backend_state.roster, {"ssh-a": {}, "ssh-b": {}})
        self.assertEqual(second.backend_state.roster, {"ssh-c": {}})
        self.assertEqual(first.backend_state.ssh_options["roster_file"], str(first.backend_state.roster_path))

    def test_prepare_keeps_different_fingerprints_in_separate_thin_payloads(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "Salt SSH backend must provide runtime-specific Thin delivery",
        )
        backend = backend_module.SaltSSHRuntimeBackend()

        first = backend.prepare(["ssh-a"], self._manifest("runtime-a"), self._context())
        second = backend.prepare(["ssh-b"], self._manifest("runtime-b"), self._context())

        self.assertNotEqual(first.backend_state.thin_dir, second.backend_state.thin_dir)
        self.assertTrue(first.backend_state.thin_dir.is_dir())
        self.assertTrue(second.backend_state.thin_dir.is_dir())

    def test_execute_delegates_the_prepared_group_to_the_salt_ssh_adapter(self) -> None:
        backend_module = self._backend_module()
        self.assertIsNotNone(
            backend_module,
            "Salt SSH backend must provide runtime-specific Thin delivery",
        )
        received = []

        def execute(prepared, command):
            received.append((prepared, command))
            return [
                ExecutionResult(
                    target=target,
                    success=True,
                    return_data={"function": command.function},
                    retcode=0,
                )
                for target in prepared.targets
            ]

        backend = backend_module.SaltSSHRuntimeBackend(command_executor=execute)
        prepared = backend.prepare(["ssh-a", "ssh-b"], self._manifest("execution"), self._context())
        command = SaltCommand(function="test.version", args=[], kwargs={})

        results = backend.execute(prepared, command)

        self.assertEqual(received, [(prepared, command)])
        self.assertEqual([result.target for result in results], ["ssh-a", "ssh-b"])
        self.assertTrue(all(result.success for result in results))

