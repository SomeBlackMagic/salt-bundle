"""Local runtime activation for permanent Salt minions."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from salt_bundle.activation.manifest import RuntimeManifest, save_manifest

from .base import (
    ExecutionResult,
    PreparedRuntime,
    RuntimeContext,
    SaltCommand,
)


_MANIFEST_PATH_OPTION = "salt_bundle_runtime_manifest_path"
_PROJECT_ROOT_OPTION = "salt_bundle_runtime_project_root"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MinionRuntimeState:
    """Paths and Salt options required to activate one local runtime."""

    manifest_path: Path
    minion_opts: Mapping[str, str]


CommandExecutor = Callable[
    [PreparedRuntime, SaltCommand], Sequence[ExecutionResult]
]


class MinionRuntimeBackend:
    """Materialize manifests for a permanent minion's local Salt runtime.

    Package contents are expected to have been installed into the minion's local
    package store before this backend is used.  The backend intentionally does
    not resolve or download dependencies during command execution.
    """

    def __init__(self, command_executor: CommandExecutor | None = None) -> None:
        self._command_executor = command_executor

    def prepare(
        self,
        targets: list[str],
        manifest: RuntimeManifest,
        context: RuntimeContext,
    ) -> PreparedRuntime:
        """Write ``manifest`` to its fingerprint-specific local runtime path."""
        started_at = perf_counter()
        manifest_path = self._manifest_path(context.cache_dir, manifest.fingerprint)
        save_manifest(manifest, manifest_path)
        state = MinionRuntimeState(
            manifest_path=manifest_path,
            minion_opts=MappingProxyType(
                {_MANIFEST_PATH_OPTION: str(manifest_path)}
                | {_PROJECT_ROOT_OPTION: str(context.project_root)}
            ),
        )
        prepared = PreparedRuntime(
            manifest=manifest,
            targets=list(targets),
            backend_state=state,
        )
        log.debug(
            "SaltBundle minion runtime: fingerprint=%s "
            "runtime_preparation_duration_ms=%.3f",
            manifest.fingerprint,
            (perf_counter() - started_at) * 1000,
        )
        return prepared

    def execute(
        self,
        prepared: PreparedRuntime,
        command: SaltCommand,
    ) -> list[ExecutionResult]:
        """Execute through the configured minion transport adapter.

        Delivery and activation are deliberately separate from transport.  A
        caller providing a Salt master/minion adapter is responsible for using
        the manifest path prepared here when it starts or refreshes the minion.
        """
        if self._command_executor is None:
            raise RuntimeError(
                "Minion command execution requires a configured transport adapter"
            )
        started_at = perf_counter()
        results = list(self._command_executor(prepared, command))
        log.debug(
            "SaltBundle minion runtime: fingerprint=%s execution_duration_ms=%.3f",
            prepared.manifest.fingerprint,
            (perf_counter() - started_at) * 1000,
        )
        return results

    @staticmethod
    def _manifest_path(cache_dir: Path, fingerprint: str) -> Path:
        """Return the stable manifest location for one runtime fingerprint."""
        return cache_dir / "runtimes" / fingerprint / "manifest.yaml"
