"""Resolve target-specific package activation without mutating project state."""

import logging
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from salt_bundle.activation.errors import (
    ExplicitConflictError,
    NamespaceCollisionError,
    PackageNotMaterializedError,
    SecurityError,
    UnknownPackageError,
)
from salt_bundle.activation.conflicts import detect_conflicts
from salt_bundle.activation.matcher import collect_packages, find_matching_rules
from salt_bundle.activation.models import (
    ActivePackageSet,
    PackageName,
    ResolvedPackage,
    compute_fingerprint,
)
from salt_bundle.activation.parser import TopBundle
from salt_bundle.dependencies.lock_models import LockFile
from salt_bundle.packaging.types import load_package_meta
from salt_bundle.utils.fs import collect_files, load_ignore_patterns


log = logging.getLogger(__name__)


class ActivationResolver:
    """Resolve the locked, locally materialized packages active for a target."""

    def __init__(
        self,
        top_bundle: TopBundle | None,
        lock_data: LockFile,
        vendor_root: Path,
        *,
        require_bundle_top: bool = False,
        top_bundle_path: Path | None = None,
    ) -> None:
        self.top_bundle = top_bundle
        self.lock_data = lock_data
        self.vendor_root = vendor_root
        self.require_bundle_top = require_bundle_top
        self.top_bundle_path = top_bundle_path or Path("top_bundle.sls")
        self._legacy_warning_emitted = False

    def resolve(
        self,
        target: str,
        *,
        saltenv: str = "base",
        grains: dict | None = None,
        pillar: dict | None = None,
    ) -> ActivePackageSet:
        """Return the immutable active package set for ``target``.

        ``grains`` and ``pillar`` are accepted for the documented API; the current
        matcher supports only exact and glob target expressions.
        """
        started_at = perf_counter()
        del grains, pillar
        if self.top_bundle is None:
            if self.require_bundle_top:
                raise FileNotFoundError(
                    f"{self.top_bundle_path.name} is required when "
                    "runtime.require_bundle_top is true"
                )
            self._warn_legacy_activation()
            direct_packages = [
                PackageName.parse(name) for name in sorted(self.lock_data.dependencies)
            ]
        else:
            environment = self.top_bundle.environments.get(saltenv)
            direct_packages = (
                collect_packages(find_matching_rules(target, environment.rules))
                if environment is not None
                else []
            )

        resolved_names = self._include_transitive_dependencies(direct_packages, saltenv)
        packages = tuple(
            self._resolved_package(package_name, saltenv)
            for package_name in resolved_names
        )
        self._raise_on_runtime_conflicts(packages)
        active_set = ActivePackageSet(
            target=target,
            saltenv=saltenv,
            packages=packages,
            fingerprint=compute_fingerprint(packages, saltenv),
        )
        duration_ms = (perf_counter() - started_at) * 1000
        log.debug(
            "SaltBundle activation: target=%s fingerprint=%s packages=[%s] "
            "resolution_duration_ms=%.3f",
            active_set.target,
            active_set.fingerprint,
            ", ".join(package.name.full_name for package in active_set.packages),
            duration_ms,
        )
        return active_set

    @staticmethod
    def _raise_on_runtime_conflicts(packages: tuple[ResolvedPackage, ...]) -> None:
        """Raise the documented activation error for the first runtime conflict."""
        metadata = {
            package.name: load_package_meta(package.path)
            for package in packages
            if (package.path / "FORMULA").is_file()
            or (package.path / "EXTENSION").is_file()
        }
        report = detect_conflicts(list(packages), metadata)
        if report.explicit:
            conflict = report.explicit[0]
            raise ExplicitConflictError(
                conflict.packages[0].name.full_name,
                conflict.packages[1].name.full_name,
            )
        if report.collisions:
            collision = report.collisions[0]
            raise NamespaceCollisionError(
                collision.path,
                [package.name.full_name for package in collision.providers],
            )

    def _warn_legacy_activation(self) -> None:
        """Log the compatibility fallback once per resolver instance."""
        if not self._legacy_warning_emitted:
            log.warning("top_bundle.sls not found; using legacy global activation mode")
            self._legacy_warning_emitted = True

    def _include_transitive_dependencies(
        self,
        direct_packages: list[PackageName],
        saltenv: str,
    ) -> list[PackageName]:
        names = list(direct_packages)
        seen = set(names)
        index = 0
        while index < len(names):
            package_name = names[index]
            entry = self._lock_entry(package_name, saltenv)
            for dependency_name in entry.dependencies:
                dependency = PackageName.parse(dependency_name)
                self._lock_entry(dependency, saltenv)
                if dependency not in seen:
                    seen.add(dependency)
                    names.append(dependency)
            index += 1
        return names

    def _resolved_package(
        self, package_name: PackageName, saltenv: str
    ) -> ResolvedPackage:
        entry = self._lock_entry(package_name, saltenv)
        path = self.vendor_root / package_name.full_name
        validate_package_path(
            path,
            self.vendor_root,
            allow_external_symlink=(entry.source_type == "path" and entry.linked),
        )
        if not path.is_dir():
            raise PackageNotMaterializedError(package_name.full_name, str(path))
        metadata = load_package_meta(path) if (path / "FORMULA").is_file() else None
        if entry.type == "formula" and getattr(metadata, "top_level_dir", None):
            state_root = path / metadata.top_level_dir
            if not state_root.is_dir():
                raise ValueError(
                    f"Formula '{package_name.full_name}' state root does not exist: {state_root}"
                )
        return ResolvedPackage(
            name=package_name,
            version=entry.version,
            package_type=entry.type,
            path=path,
            digest=entry.digest,
        )

    def _lock_entry(self, package_name: PackageName, saltenv: str):
        try:
            return self.lock_data.dependencies[package_name.full_name]
        except KeyError as exc:
            raise UnknownPackageError(package_name.full_name, saltenv) from exc


def validate_package_path(
    path: Path,
    allowed_root: Path,
    *,
    allow_external_symlink: bool = False,
) -> None:
    """Raise ``SecurityError`` when ``path`` resolves outside ``allowed_root``."""
    resolved_path = path.resolve()
    resolved_root = allowed_root.resolve()
    if not resolved_path.is_relative_to(resolved_root) and not allow_external_symlink:
        raise SecurityError(f"Package path '{path}' escapes root '{allowed_root}'")


def verify_package_digest(package_path: Path, expected_digest: str) -> None:
    """Raise ``SecurityError`` if a package tree differs from its expected digest.

    The canonical hash is SHA-256 over every regular file sorted by its relative
    POSIX path.  Each path and file content is separated by a NUL byte so two
    distinct trees cannot have an ambiguous byte representation.
    """
    if expected_digest == "linked":
        return
    if not expected_digest.startswith("sha256:") or len(expected_digest) != 71:
        raise SecurityError(f"Invalid package digest: {expected_digest!r}")
    try:
        int(expected_digest.removeprefix("sha256:"), 16)
    except ValueError as exc:
        raise SecurityError(f"Invalid package digest: {expected_digest!r}") from exc

    if not package_path.is_dir():
        raise SecurityError(f"Package path '{package_path}' is not a directory")

    digest = sha256()
    for child_path in sorted(package_path.rglob("*")):
        if child_path.is_symlink():
            raise SecurityError(f"Package path '{child_path}' contains a symlink")
    metadata_file = (
        package_path / "FORMULA"
        if (package_path / "FORMULA").is_file()
        else package_path / "EXTENSION"
    )
    files = collect_files(package_path, load_ignore_patterns(package_path))
    if metadata_file.is_file() and metadata_file not in files:
        files.append(metadata_file)
    for child_path in sorted(files):
        relative_path = child_path.relative_to(package_path).as_posix()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        with child_path.open("rb") as package_file:
            for chunk in iter(lambda: package_file.read(8192), b""):
                digest.update(chunk)
        digest.update(b"\0")

    actual_digest = f"sha256:{digest.hexdigest()}"
    if actual_digest != expected_digest:
        raise SecurityError(
            f"Package digest mismatch for '{package_path}': "
            f"expected {expected_digest}, got {actual_digest}"
        )
