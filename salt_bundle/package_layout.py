"""Resolve Salt package layouts independently of package source."""

from __future__ import annotations

from pathlib import Path
from typing import Literal


PackageType = Literal["formula", "extension"]


def detect_package_type(package_path: Path) -> PackageType:
    """Return the package layout type detected from its package root."""
    if (package_path / "EXTENSION").is_file() or (package_path / "src" / "saltext").is_dir():
        return "extension"
    return "formula"


def detect_extension_name(package_path: Path) -> str | None:
    """Return the sole saltext package name, when it can be determined."""
    saltext_dir = package_path / "src" / "saltext"
    if not saltext_dir.is_dir():
        return None
    names = [item.name for item in saltext_dir.iterdir() if item.is_dir() and not item.name.startswith("_")]
    return names[0] if len(names) == 1 else None


def resolve_namespace_dir(
    package_path: Path,
    package_type: PackageType,
    namespace: str,
) -> Path | None:
    """Return the physical directory for a logical Salt loader namespace."""
    if package_type == "formula":
        candidate = package_path / f"_{namespace}"
    else:
        extension_name = detect_extension_name(package_path)
        if extension_name is None:
            return None
        candidate = package_path / "src" / "saltext" / extension_name / namespace
    return candidate if candidate.is_dir() else None


def discover_package_paths(vendor_path: Path) -> list[Path]:
    """Discover packages in two-level vendor trees and legacy package roots."""
    if not vendor_path.is_dir():
        return []

    packages: list[Path] = []
    for vendor_or_package in sorted(vendor_path.iterdir()):
        if vendor_or_package.name.startswith(".") or not vendor_or_package.is_dir():
            continue
        if _is_package_root(vendor_or_package):
            packages.append(vendor_or_package.resolve() if vendor_or_package.is_symlink() else vendor_or_package)
            continue
        for package in sorted(vendor_or_package.iterdir()):
            if package.name.startswith(".") or not package.is_dir():
                continue
            packages.append(package.resolve() if package.is_symlink() else package)
    return packages


def _is_package_root(path: Path) -> bool:
    return (
        (path / "FORMULA").is_file()
        or (path / "EXTENSION").is_file()
        or (path / "src" / "saltext").is_dir()
        or any(item.is_dir() and item.name.startswith("_") for item in path.iterdir())
    )
