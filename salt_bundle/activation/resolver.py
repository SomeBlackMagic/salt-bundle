"""Resolve target-specific package activation without mutating project state."""

import logging
from hashlib import sha256
from pathlib import Path

from salt_bundle.activation.errors import (
    PackageNotMaterializedError,
    SecurityError,
    UnknownPackageError,
)
from salt_bundle.activation.matcher import collect_packages, find_matching_rules
from salt_bundle.activation.models import (
    ActivePackageSet,
    PackageName,
    ResolvedPackage,
    compute_fingerprint,
)
from salt_bundle.activation.parser import TopBundle
from salt_bundle.dependencies.lock_models import LockFile


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
        return ActivePackageSet(
            target=target,
            saltenv=saltenv,
            packages=packages,
            fingerprint=compute_fingerprint(packages, saltenv),
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
        validate_package_path(path, self.vendor_root)
        if not path.is_dir():
            raise PackageNotMaterializedError(package_name.full_name, str(path))
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


def validate_package_path(path: Path, allowed_root: Path) -> None:
    """Raise ``SecurityError`` when ``path`` resolves outside ``allowed_root``."""
    resolved_path = path.resolve()
    resolved_root = allowed_root.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise SecurityError(f"Package path '{path}' escapes root '{allowed_root}'")


def verify_package_digest(package_path: Path, expected_digest: str) -> None:
    """Raise ``SecurityError`` if a package tree differs from its expected digest.

    The canonical hash is SHA-256 over every regular file sorted by its relative
    POSIX path.  Each path and file content is separated by a NUL byte so two
    distinct trees cannot have an ambiguous byte representation.
    """
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
        if child_path.is_file():
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
