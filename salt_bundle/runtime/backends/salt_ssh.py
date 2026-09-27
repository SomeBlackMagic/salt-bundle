"""Runtime-specific Thin payload delivery for Salt SSH."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

import yaml

from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest
from salt_bundle.package_layout import resolve_namespace_dir as _resolve_namespace_dir

from .base import ExecutionResult, PreparedRuntime, RuntimeContext, SaltCommand


_NAMESPACES = (
    "auth",
    "beacons",
    "cache",
    "cloud",
    "engines",
    "executors",
    "grains",
    "log_handlers",
    "matchers",
    "metaproxy",
    "modules",
    "netapi",
    "output",
    "pillar",
    "pkgdb",
    "pkgfiles",
    "proxy",
    "queues",
    "renderers",
    "returners",
    "roster",
    "runners",
    "sdb",
    "serializers",
    "states",
    "thorium",
    "tokens",
    "tops",
    "utils",
    "wheel",
    "wrapper",
)


@dataclass(frozen=True)
class SaltSSHRuntimeState:
    """Thin payload and Salt SSH options for one execution group."""

    thin_dir: Path
    roster_path: Path
    roster: Mapping[str, Mapping[str, str]]
    ssh_options: Mapping[str, str]


CommandExecutor = Callable[[PreparedRuntime, SaltCommand], Sequence[ExecutionResult]]


class SaltSSHRuntimeBackend:
    """Prepare isolated Thin payloads and delegate Salt SSH execution.

    The payload is cached by manifest fingerprint. Roster data is intentionally
    generated per ``prepare`` call because it belongs to an execution group,
    rather than to the reusable runtime payload.
    """

    def __init__(self, command_executor: CommandExecutor | None = None) -> None:
        self._command_executor = command_executor

    def prepare(
        self,
        targets: list[str],
        manifest: RuntimeManifest,
        context: RuntimeContext,
    ) -> PreparedRuntime:
        """Materialize one fingerprint-specific Thin payload and group roster."""
        runtime_dir = context.cache_dir / "runtimes" / manifest.fingerprint
        thin_dir = runtime_dir / "thin"
        if not thin_dir.exists():
            self._materialize_thin(thin_dir, manifest, context.project_root)

        roster = {target: {} for target in targets}
        roster_path = runtime_dir / f"roster-{self._group_key(targets)}.yaml"
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(yaml.safe_dump(roster, sort_keys=True), encoding="utf-8")
        state = SaltSSHRuntimeState(
            thin_dir=thin_dir,
            roster_path=roster_path,
            roster=MappingProxyType(roster),
            ssh_options=MappingProxyType({"roster_file": str(roster_path)}),
        )
        return PreparedRuntime(
            manifest=manifest,
            targets=list(targets),
            backend_state=state,
        )

    def execute(
        self,
        prepared: PreparedRuntime,
        command: SaltCommand,
    ) -> list[ExecutionResult]:
        """Execute the prepared group through the configured Salt SSH adapter."""
        if self._command_executor is None:
            raise RuntimeError(
                "Salt SSH command execution requires a configured transport adapter"
            )
        return list(self._command_executor(prepared, command))

    @staticmethod
    def _group_key(targets: list[str]) -> str:
        """Return a filesystem-safe, deterministic roster key for targets."""
        return hashlib.sha256("\0".join(targets).encode()).hexdigest()

    @classmethod
    def _materialize_thin(
        cls,
        thin_dir: Path,
        manifest: RuntimeManifest,
        project_root: Path,
    ) -> None:
        """Copy active Salt namespaces into a Thin staging directory."""
        thin_dir.mkdir(parents=True, exist_ok=True)
        for package in manifest.packages:
            package_path = project_root / package.path
            if not package_path.is_dir():
                raise FileNotFoundError(
                    f"Runtime package path does not exist: {package_path}"
                )
            for namespace in _NAMESPACES:
                source = _resolve_namespace_dir(
                    package_path, package.package_type, namespace
                )
                if source is None:
                    continue
                destination = cls._destination_for(
                    source, package, namespace, thin_dir
                )
                shutil.copytree(source, destination, dirs_exist_ok=True)
                cls._copy_extension_init(source, package, namespace, thin_dir)

    @staticmethod
    def _destination_for(
        source: Path,
        package: ManifestPackageEntry,
        namespace: str,
        thin_dir: Path,
    ) -> Path:
        """Map a package namespace to its physical Thin payload location."""
        if package.package_type == "formula":
            return thin_dir / f"_{namespace}"
        extension_root = source.parent
        return thin_dir / "saltext" / extension_root.name / namespace

    @staticmethod
    def _copy_extension_init(
        source: Path,
        package: ManifestPackageEntry,
        namespace: str,
        thin_dir: Path,
    ) -> None:
        """Preserve an extension package marker when materializing its namespace."""
        if package.package_type != "extension":
            return
        extension_root = source.parent
        source_init = extension_root / "__init__.py"
        if source_init.is_file():
            destination = thin_dir / "saltext" / extension_root.name / "__init__.py"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_init, destination)
