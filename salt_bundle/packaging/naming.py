"""Validation and canonical formatting for package identifiers."""

import re
from dataclasses import dataclass


LEGACY_VENDOR = "legacy"

NAMESPACED_NAME_PATTERN = re.compile(
    r"^(?P<vendor>(?![a-z0-9-]*--)[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?)/"
    r"(?P<package>(?![a-z0-9_-]*--)[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?)$"
)
LEGACY_NAME_PATTERN = re.compile(
    r"^(?![a-z0-9_-]*--)[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$"
)


@dataclass(frozen=True)
class PackageName:
    """A canonical ``vendor/package`` package identifier."""

    vendor: str
    package: str

    @classmethod
    def parse(cls, name: str) -> "PackageName":
        """Parse a strict ``vendor/package`` identifier."""
        match = NAMESPACED_NAME_PATTERN.fullmatch(name)
        if match is None:
            raise ValueError(
                f"Invalid package name: {name!r}. Expected format: vendor/package"
            )
        return cls(vendor=match["vendor"], package=match["package"])

    @property
    def full_name(self) -> str:
        """Return the canonical package identifier."""
        return f"{self.vendor}/{self.package}"

    @property
    def archive_prefix(self) -> str:
        """Return the filename-safe ``vendor--package`` prefix."""
        return f"{self.vendor}--{self.package}"

    def __str__(self) -> str:
        return self.full_name


def validate_package_name(name: str) -> bool:
    """Return whether ``name`` is a strict ``vendor/package`` identifier."""
    return NAMESPACED_NAME_PATTERN.fullmatch(name) is not None


def validate_metadata_package_name(name: str) -> bool:
    """Allow strict names and legacy single-part names in package metadata."""
    return validate_package_name(name) or LEGACY_NAME_PATTERN.fullmatch(name) is not None


def canonicalize_package_name(name: str) -> PackageName:
    """Return a canonical identifier, mapping legacy metadata into ``legacy``."""
    if validate_package_name(name):
        return PackageName.parse(name)
    if LEGACY_NAME_PATTERN.fullmatch(name):
        return PackageName(vendor=LEGACY_VENDOR, package=name)
    raise ValueError(
        f"Invalid package name: {name!r}. Expected format: vendor/package"
    )


def archive_filename(name: str, version: str) -> str:
    """Build a filename-safe archive name from metadata or canonical package name."""
    package_name = canonicalize_package_name(name)
    return f"{package_name.archive_prefix}-{version}.tgz"
