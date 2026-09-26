"""Models for target-aware package activation."""

from dataclasses import dataclass
import re


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
