"""Models for target-aware package activation."""

from hashlib import sha256
from pathlib import Path
from typing import Iterable, Literal

from dataclasses import dataclass

from ..packaging.naming import PackageName


@dataclass(frozen=True)
class ResolvedPackage:
    """An exact package version materialized in the local package store."""

    name: PackageName
    version: str
    package_type: Literal["formula", "extension"]
    path: Path
    digest: str


@dataclass(frozen=True)
class ActivePackageSet:
    """The immutable package set available to one target and environment."""

    target: str
    saltenv: str
    packages: tuple[ResolvedPackage, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        """Store packages as an immutable tuple."""
        object.__setattr__(self, "packages", tuple(self.packages))


def compute_fingerprint(
    packages: Iterable[ResolvedPackage], saltenv: str
) -> str:
    """Compute a stable SHA-256 fingerprint for an activated package set."""
    package_lines = [
        f"{package.name.full_name}@{package.version}:{package.digest}"
        for package in sorted(packages, key=lambda package: package.name.full_name)
    ]
    canonical_value = "\n".join((f"saltenv:{saltenv}", *package_lines))
    return sha256(canonical_value.encode("utf-8")).hexdigest()
