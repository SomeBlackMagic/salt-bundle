"""Models for target-aware package activation."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable, Literal


_PACKAGE_NAME_PATTERN = re.compile(
    r"^(?P<vendor>[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)/"
    r"(?P<package>[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)$"
)


@dataclass(frozen=True)
class PackageName:
    """A package identifier in the vendor/package namespace."""

    vendor: str
    package: str

    @classmethod
    def parse(cls, name: str) -> "PackageName":
        """Parse a ``vendor/package`` identifier."""
        match = _PACKAGE_NAME_PATTERN.fullmatch(name)
        if match is None:
            raise ValueError(f"Invalid package name: {name!r}")

        return cls(vendor=match["vendor"], package=match["package"])

    @property
    def full_name(self) -> str:
        """Return the canonical vendor/package identifier."""
        return f"{self.vendor}/{self.package}"

    def __str__(self) -> str:
        return self.full_name


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
