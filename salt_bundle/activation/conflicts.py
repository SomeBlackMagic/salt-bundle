"""Detect conflicts in a target's active package set."""

from dataclasses import dataclass

from salt_bundle.activation.models import PackageName, ResolvedPackage
from salt_bundle.packaging.types import PackageMetadata
from salt_bundle.package_layout import resolve_namespace_dir


SALT_LOADER_NAMESPACES = {
    "beacons",
    "engines",
    "grains",
    "modules",
    "output",
    "pillar",
    "proxy",
    "renderers",
    "returners",
    "runners",
    "states",
    "utils",
}


@dataclass(frozen=True)
class ExplicitConflict:
    """An active pair of packages declared mutually incompatible."""

    packages: tuple[ResolvedPackage, ResolvedPackage]


@dataclass(frozen=True)
class NamespaceCollision:
    """A Salt loader file supplied by more than one active package."""

    path: str
    providers: tuple[ResolvedPackage, ...]


@dataclass
class ConflictReport:
    """All conflicts found in an active package set."""

    explicit: list[ExplicitConflict]
    collisions: list[NamespaceCollision]

    @property
    def has_conflicts(self) -> bool:
        """Return whether any conflict was found."""
        return bool(self.explicit or self.collisions)


def check_explicit_conflicts(
    packages: list[ResolvedPackage],
    metadata: dict[PackageName, PackageMetadata],
) -> list[ExplicitConflict]:
    """Return declared conflicts for packages that are both active."""
    packages_by_name = {package.name: package for package in packages}
    conflicts: list[ExplicitConflict] = []
    reported_pairs: set[frozenset[PackageName]] = set()

    for package in packages:
        package_metadata = metadata.get(package.name)
        if package_metadata is None:
            continue
        for entry in getattr(package_metadata, "conflicts", []):
            conflicting_name = PackageName.parse(entry.name)
            conflicting_package = packages_by_name.get(conflicting_name)
            if conflicting_package is None or conflicting_package == package:
                continue

            pair = frozenset((package.name, conflicting_name))
            if pair in reported_pairs:
                continue
            reported_pairs.add(pair)
            conflicts.append(ExplicitConflict((package, conflicting_package)))

    return conflicts


def check_namespace_collisions(
    packages: list[ResolvedPackage],
) -> list[NamespaceCollision]:
    """Scan active packages for files duplicated in Salt loader namespaces."""
    providers_by_path: dict[str, list[ResolvedPackage]] = {}
    for package in packages:
        for namespace in SALT_LOADER_NAMESPACES:
            namespace_path = resolve_namespace_dir(
                package.path, package.package_type, namespace
            )
            if namespace_path is None:
                continue
            for candidate in namespace_path.rglob("*"):
                if candidate.is_file():
                    path = f"_{namespace}/{candidate.relative_to(namespace_path).as_posix()}"
                    providers_by_path.setdefault(path, []).append(package)

    return [
        NamespaceCollision(path, tuple(providers))
        for path, providers in sorted(providers_by_path.items())
        if len(providers) > 1
    ]


def detect_conflicts(
    packages: list[ResolvedPackage],
    metadata: dict[PackageName, PackageMetadata],
) -> ConflictReport:
    """Run all conflict checks and return a report that may be empty."""
    return ConflictReport(
        explicit=check_explicit_conflicts(packages, metadata),
        collisions=check_namespace_collisions(packages),
    )
