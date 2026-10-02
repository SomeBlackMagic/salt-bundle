"""Tests for the runtime backend protocol and its shared models."""

import importlib.util
import typing
from pathlib import Path
import unittest

from salt_bundle.activation.manifest import RuntimeManifest
from salt_bundle.dependencies.saltfile_models import RuntimeConfig


class TestRuntimeBackendContract(unittest.TestCase):
    """Specify the backend-independent runtime execution interface."""

    @staticmethod
    def _backend_module():
        try:
            spec = importlib.util.find_spec("salt_bundle.runtime.backends.base")
        except ModuleNotFoundError:
            return None
        if spec is None:
            return None

        from salt_bundle.runtime.backends import base

        return base

    @staticmethod
    def _manifest() -> RuntimeManifest:
        return RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint="f" * 64,
            packages=(),
        )

    def test_runtime_context_keeps_runtime_paths_and_configuration(self) -> None:
        backend = self._backend_module()
        self.assertIsNotNone(
            backend,
            "runtime backend base module must define the shared runtime contract",
        )

        config = RuntimeConfig(cache_dir=".salt-bundle/runtimes", max_workers=2)
        context = backend.RuntimeContext(
            project_root=Path("/project"),
            vendor_root=Path("/project/vendor"),
            cache_dir=Path("/project/.salt-bundle/runtimes"),
            config=config,
        )

        self.assertEqual(context.project_root, Path("/project"))
        self.assertEqual(context.vendor_root, Path("/project/vendor"))
        self.assertEqual(context.cache_dir, Path("/project/.salt-bundle/runtimes"))
        self.assertIs(context.config, config)

    def test_mock_backend_conforms_to_protocol_and_receives_context(self) -> None:
        backend = self._backend_module()
        self.assertIsNotNone(
            backend,
            "runtime backend base module must define RuntimeBackend",
        )

        manifest = self._manifest()
        context = backend.RuntimeContext(
            project_root=Path("/project"),
            vendor_root=Path("/project/vendor"),
            cache_dir=Path("/project/.salt-bundle/runtimes"),
            config=RuntimeConfig(),
        )

        class RecordingBackend:
            def prepare(self, targets, received_manifest, received_context):
                self.targets = targets
                self.manifest = received_manifest
                self.context = received_context
                return backend.PreparedRuntime(
                    manifest=received_manifest,
                    targets=targets,
                    backend_state={"prepared": True},
                )

            def execute(self, prepared, command):
                return [
                    backend.ExecutionResult(
                        target=target,
                        success=True,
                        return_data={"function": command.function},
                        retcode=0,
                    )
                    for target in prepared.targets
                ]

        runtime_backend = RecordingBackend()
        self.assertIsInstance(runtime_backend, backend.RuntimeBackend)

        prepared = runtime_backend.prepare(["web-01", "web-02"], manifest, context)

        self.assertEqual(prepared.manifest, manifest)
        self.assertEqual(prepared.targets, ["web-01", "web-02"])
        self.assertEqual(prepared.backend_state, {"prepared": True})
        self.assertIs(runtime_backend.context, context)

    def test_execute_returns_one_execution_result_per_target(self) -> None:
        backend = self._backend_module()
        self.assertIsNotNone(
            backend,
            "runtime backend base module must define execution result models",
        )

        manifest = self._manifest()
        prepared = backend.PreparedRuntime(
            manifest=manifest,
            targets=["web-01", "web-02"],
            backend_state=None,
        )
        command = backend.SaltCommand(
            function="test.version",
            args=["--verbose"],
            kwargs={"timeout": 30},
        )

        class SuccessfulBackend:
            def prepare(self, targets, received_manifest, context):
                return prepared

            def execute(self, received_prepared, received_command):
                return [
                    backend.ExecutionResult(
                        target=target,
                        success=True,
                        return_data={"function": received_command.function},
                        retcode=0,
                    )
                    for target in received_prepared.targets
                ]

        results = SuccessfulBackend().execute(prepared, command)

        self.assertEqual([result.target for result in results], ["web-01", "web-02"])
        self.assertTrue(all(result.success for result in results))
        self.assertEqual([result.retcode for result in results], [0, 0])
        self.assertEqual(
            [result.return_data for result in results],
            [{"function": "test.version"}, {"function": "test.version"}],
        )

    def test_protocol_execute_declares_list_return_type(self) -> None:
        """RuntimeBackend.execute() must declare list[ExecutionResult] return type.

        Regression test for bug #001: the Protocol declared a bare
        ``ExecutionResult`` return while every implementation and the executor
        rely on ``list[ExecutionResult]``.
        """
        backend = self._backend_module()
        self.assertIsNotNone(backend, "runtime backend base module must be importable")

        hints = typing.get_type_hints(backend.RuntimeBackend.execute)
        expected = list[backend.ExecutionResult]
        self.assertEqual(
            hints["return"],
            expected,
            f"RuntimeBackend.execute() return type must be list[ExecutionResult], "
            f"got {hints['return']}",
        )
