"""Resolve target-specific package activation without mutating project state."""

from pathlib import Path

from salt_bundle.activation.errors import (
    PackageNotMaterializedError,
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


class ActivationResolver:
    """Resolve the locked, locally materialized packages active for a target."""

    def __init__(
        self,
        top_bundle: TopBundle,
        lock_data: LockFile,
        vendor_root: Path,
    ) -> None:
        self.top_bundle = top_bundle
        self.lock_data = lock_data
        self.vendor_root = vendor_root

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
