"""Shared contract for runtime delivery backends."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from salt_bundle.activation.manifest import RuntimeManifest
from salt_bundle.dependencies.saltfile_models import RuntimeConfig


@dataclass
class RuntimeContext:
    """Project paths and configuration needed to prepare a runtime."""

    project_root: Path
    vendor_root: Path
    cache_dir: Path
    config: RuntimeConfig


@dataclass
class SaltCommand:
    """A Salt function invocation."""

    function: str
    args: list[str]
    kwargs: dict[str, Any]


@dataclass
class PreparedRuntime:
    """A runtime prepared by a backend for a target group."""

    manifest: RuntimeManifest
    targets: list[str]
    backend_state: Any


@dataclass
class ExecutionResult:
    """The outcome of executing a command for one target."""

    target: str
    success: bool
    return_data: Any
    retcode: int


@runtime_checkable
class RuntimeBackend(Protocol):
    """Prepare a runtime and execute Salt commands through it."""

    def prepare(
        self,
        targets: list[str],
        manifest: RuntimeManifest,
        context: RuntimeContext,
    ) -> PreparedRuntime:
        """Prepare ``manifest`` for the supplied targets."""

    def execute(
        self,
        prepared: PreparedRuntime,
        command: SaltCommand,
    ) -> ExecutionResult:
        """Execute ``command`` through a prepared runtime."""
