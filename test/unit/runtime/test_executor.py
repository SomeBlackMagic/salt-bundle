"""Tests for parallel execution of runtime groups."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import threading
import time
import unittest

from salt_bundle.activation.manifest import RuntimeManifest
from salt_bundle.dependencies.saltfile_models import RuntimeConfig
from salt_bundle.runtime.backends.base import ExecutionResult, PreparedRuntime, SaltCommand
from salt_bundle.runtime.grouping import RuntimeGroup


class RecordingBackend:
    """Backend fake that records independent prepare/execute calls."""

    def __init__(self, *, delay: float = 0, failing_fingerprints: set[str] | None = None):
        self.delay = delay
        self.failing_fingerprints = failing_fingerprints or set()
        self.calls: list[tuple[str, list[str], int]] = []
        self._lock = threading.Lock()

    def prepare(self, targets, manifest, context):
        return PreparedRuntime(manifest=manifest, targets=list(targets), backend_state=None)

    def execute(self, prepared, command):
        del command
        with self._lock:
            self.calls.append(
                (
                    prepared.manifest.fingerprint,
                    prepared.targets,
                    threading.get_ident(),
                )
            )
        if prepared.manifest.fingerprint in self.failing_fingerprints:
            raise RuntimeError(f"failed {prepared.manifest.fingerprint}")
        if self.delay:
            time.sleep(self.delay)
        return [
            ExecutionResult(
                target=target,
                success=True,
                return_data={"target": target},
                retcode=0,
            )
            for target in prepared.targets
        ]


class TestParallelExecutor(unittest.TestCase):
    """Specify concurrent, isolated execution for runtime groups."""

    @staticmethod
    def _executor_module():
        spec = importlib.util.find_spec("salt_bundle.runtime.executor")
        assert spec is not None, "runtime must provide a parallel executor module"

        from salt_bundle.runtime import executor

        return executor

    @staticmethod
    def _context():
        from salt_bundle.runtime.backends.base import RuntimeContext

        return RuntimeContext(
            project_root=Path("/project"),
            vendor_root=Path("/project/vendor"),
            cache_dir=Path("/project/.salt-bundle/runtimes"),
            config=RuntimeConfig(),
        )

    @staticmethod
    def _groups(*fingerprints: str) -> dict[str, RuntimeGroup]:
        return {
            fingerprint: RuntimeGroup(
                fingerprint=fingerprint,
                targets=[f"{fingerprint}-01"],
                manifest=RuntimeManifest(
                    schema_version=1,
                    saltenv="base",
                    fingerprint=fingerprint,
                    packages=(),
                ),
            )
            for fingerprint in fingerprints
        }

    @staticmethod
    def _command() -> SaltCommand:
        return SaltCommand(function="test.version", args=[], kwargs={})

    def test_executes_one_group_and_aggregates_results_by_target(self) -> None:
        executor = self._executor_module()
        backend = RecordingBackend()
        groups = self._groups("runtime-a")

        result = executor.execute_parallel(
            groups, backend, self._context(), self._command()
        )

        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(result.group_results), 1)
        group_result = result.group_results[0]
        self.assertIs(group_result.group, groups["runtime-a"])
        self.assertTrue(group_result.success)
        self.assertIsNone(group_result.error)
        self.assertEqual([item.target for item in group_result.results], ["runtime-a-01"])
        self.assertEqual(backend.calls[0][:2], ("runtime-a", ["runtime-a-01"]))

    def test_executes_groups_concurrently_up_to_max_workers(self) -> None:
        executor = self._executor_module()
        backend = RecordingBackend(delay=0.2)
        groups = self._groups("runtime-a", "runtime-b")

        started_at = time.monotonic()
        result = executor.execute_parallel(
            groups, backend, self._context(), self._command(), max_workers=2
        )
        elapsed = time.monotonic() - started_at

        self.assertTrue(result.success)
        self.assertLess(elapsed, 0.35)
        self.assertEqual(len({call[2] for call in backend.calls}), 2)

    def test_honors_max_workers_without_losing_group_isolation(self) -> None:
        executor = self._executor_module()
        backend = RecordingBackend(delay=0.1)
        groups = self._groups("runtime-a", "runtime-b", "runtime-c")

        result = executor.execute_parallel(
            groups, backend, self._context(), self._command(), max_workers=1
        )

        self.assertTrue(result.success)
        self.assertEqual(len({call[2] for call in backend.calls}), 1)
        self.assertEqual(
            {fingerprint for fingerprint, _, _ in backend.calls}, set(groups)
        )
        self.assertTrue(
            all(
                group_result.results[0].target == group_result.group.targets[0]
                for group_result in result.group_results
            )
        )

    def test_continues_other_groups_and_returns_exit_code_one_after_a_failure(self) -> None:
        executor = self._executor_module()
        backend = RecordingBackend(failing_fingerprints={"runtime-b"})
        groups = self._groups("runtime-a", "runtime-b", "runtime-c")

        result = executor.execute_parallel(
            groups, backend, self._context(), self._command(), max_workers=3
        )

        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        by_fingerprint = {
            group_result.group.fingerprint: group_result
            for group_result in result.group_results
        }
        self.assertTrue(by_fingerprint["runtime-a"].success)
        self.assertFalse(by_fingerprint["runtime-b"].success)
        self.assertIsInstance(by_fingerprint["runtime-b"].error, RuntimeError)
        self.assertEqual(by_fingerprint["runtime-b"].results, [])
        self.assertTrue(by_fingerprint["runtime-c"].success)
        self.assertEqual({call[0] for call in backend.calls}, set(groups))

