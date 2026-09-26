"""Portable manifests for activated Salt package runtimes."""

from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Any, Literal

import yaml

from .errors import RuntimeManifestError
from .models import ActivePackageSet, PackageName


_SCHEMA_VERSION = 1
_PACKAGE_TYPES = {"formula", "extension"}


@dataclass(frozen=True)
class ManifestPackageEntry:
    """One exact package available in a runtime manifest."""

    name: PackageName
    version: str
    package_type: Literal["formula", "extension"]
    digest: str
    path: str


@dataclass(frozen=True)
class RuntimeManifest:
    """A versioned, backend-independent activated package set."""

    schema_version: int
    saltenv: str
    fingerprint: str
    packages: tuple[ManifestPackageEntry, ...]

    def __post_init__(self) -> None:
        """Keep package entries immutable even when supplied as an iterable."""
        object.__setattr__(self, "packages", tuple(self.packages))


def build_manifest(active_set: ActivePackageSet) -> RuntimeManifest:
    """Build a portable manifest from an activated package set."""
    entries = tuple(
        ManifestPackageEntry(
            name=package.name,
            version=package.version,
            package_type=package.package_type,
            digest=package.digest,
            path=_relative_package_path(package.path),
        )
        for package in sorted(
            active_set.packages, key=lambda package: package.name.full_name
        )
    )
    return RuntimeManifest(
        schema_version=_SCHEMA_VERSION,
        saltenv=active_set.saltenv,
        fingerprint=active_set.fingerprint,
        packages=entries,
    )


def serialize_manifest(manifest: RuntimeManifest) -> str:
    """Serialize a runtime manifest as YAML."""
    return yaml.safe_dump(
        {
            "schema": manifest.schema_version,
            "saltenv": manifest.saltenv,
            "fingerprint": manifest.fingerprint,
            "packages": [
                {
                    "name": package.name.full_name,
                    "version": package.version,
                    "type": package.package_type,
                    "digest": package.digest,
                    "path": package.path,
                }
                for package in manifest.packages
            ],
        },
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def deserialize_manifest(content: str) -> RuntimeManifest:
    """Deserialize and validate a runtime manifest YAML document."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise RuntimeManifestError("Invalid runtime manifest YAML") from exc

    if not isinstance(data, dict):
        raise RuntimeManifestError("Runtime manifest must be a mapping")

    schema_version = _required_value(data, "schema", int)
    if schema_version != _SCHEMA_VERSION:
        raise RuntimeManifestError(
            f"Unsupported runtime manifest schema: {schema_version}"
        )

    saltenv = _required_value(data, "saltenv", str)
    fingerprint = _required_value(data, "fingerprint", str)
    packages_data = _required_value(data, "packages", list)
    packages = tuple(_deserialize_package(item) for item in packages_data)
    return RuntimeManifest(
        schema_version=schema_version,
        saltenv=saltenv,
        fingerprint=fingerprint,
        packages=packages,
    )


def save_manifest(manifest: RuntimeManifest, path: Path) -> None:
    """Save a runtime manifest to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_manifest(manifest), encoding="utf-8")


def load_manifest(path: Path) -> RuntimeManifest:
    """Load and validate a runtime manifest from a YAML file."""
    return deserialize_manifest(path.read_text(encoding="utf-8"))


def _deserialize_package(data: Any) -> ManifestPackageEntry:
    if not isinstance(data, dict):
        raise RuntimeManifestError("Runtime manifest package entries must be mappings")

    name = _required_value(data, "name", str)
    package_type = _required_value(data, "type", str)
    if package_type not in _PACKAGE_TYPES:
        raise RuntimeManifestError(f"Unsupported runtime package type: {package_type}")

    path = _required_value(data, "path", str)
    if not _is_relative_path(path):
        raise RuntimeManifestError("Runtime manifest package paths must be relative")

    try:
        package_name = PackageName.parse(name)
    except ValueError as exc:
        raise RuntimeManifestError(f"Invalid runtime manifest package name: {name!r}") from exc

    return ManifestPackageEntry(
        name=package_name,
        version=_required_value(data, "version", str),
        package_type=package_type,
        digest=_required_value(data, "digest", str),
        path=path,
    )


def _required_value(data: dict[str, Any], key: str, value_type: type) -> Any:
    value = data.get(key)
    if key not in data or not isinstance(value, value_type):
        raise RuntimeManifestError(f"Runtime manifest field '{key}' is required")
    return value


def _relative_package_path(path: Path) -> str:
    value = str(path)
    if not _is_relative_path(value):
        raise RuntimeManifestError("Runtime manifest package paths must be relative")
    return value


def _is_relative_path(path: str) -> bool:
    pure_path = PurePath(path)
    return not pure_path.is_absolute() and ".." not in pure_path.parts
