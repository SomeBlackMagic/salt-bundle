"""Vendor directory management."""

import shutil
from pathlib import Path

from .package import unpack_formula


def get_vendor_dir(project_dir: Path | str, vendor_dir_name: str = "vendor") -> Path:
    """Get vendor directory path.

    Args:
        project_dir: Project directory
        vendor_dir_name: Vendor directory name

    Returns:
        Path to vendor directory
    """
    return Path(project_dir) / vendor_dir_name


def ensure_vendor_dir(vendor_dir: Path) -> None:
    """Ensure vendor directory exists.

    Args:
        vendor_dir: Vendor directory path
    """
    vendor_dir.mkdir(parents=True, exist_ok=True)


def clear_vendor_dir(vendor_dir: Path) -> None:
    """Clear vendor directory contents.

    Args:
        vendor_dir: Vendor directory path
    """
    if vendor_dir.exists():
        for item in vendor_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def install_package_to_vendor(
    archive_path: Path,
    package_name: str,
    vendor_dir: Path
) -> Path:
    """Install package to vendor directory.

    Args:
        archive_path: Path to package archive
        package_name: Package name
        vendor_dir: Vendor directory path

    Returns:
        Path to installed package directory
    """
    target_dir = vendor_dir / package_name

    # Remove existing installation
    if target_dir.exists():
        shutil.rmtree(target_dir)

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Unpack formula
    unpack_formula(archive_path, target_dir)

    return target_dir


def symlink_path_package_to_vendor(
    source_path: Path | str,
    package_name: str,
    vendor_dir: Path
) -> Path:
    """Install a path-type package by symlinking the source directory into vendor.

    Args:
        source_path: Absolute path to the local formula directory
        package_name: Package name (used as the vendor subdirectory name)
        vendor_dir: Vendor directory path

    Returns:
        Path to the symlink in the vendor directory
    """
    source_path = Path(source_path).resolve()
    target_link = vendor_dir / package_name

    if target_link.exists() or target_link.is_symlink():
        if target_link.is_symlink():
            target_link.unlink()
        elif target_link.is_dir():
            shutil.rmtree(target_link)
        else:
            target_link.unlink()

    target_link.symlink_to(source_path)
    return target_link


def is_package_installed(package_name: str, vendor_dir: Path) -> bool:
    """Check if package is installed in vendor directory.

    Args:
        package_name: Package name
        vendor_dir: Vendor directory path

    Returns:
        True if package is installed
    """
    package_dir = vendor_dir / package_name
    return package_dir.exists() and (package_dir / '.saltbundle.yaml').exists()


def get_installed_packages(vendor_dir: Path) -> list[str]:
    """Get list of installed packages in vendor directory.

    Args:
        vendor_dir: Vendor directory path

    Returns:
        List of package names
    """
    if not vendor_dir.exists():
        return []

    packages = []
    for item in vendor_dir.iterdir():
        if item.is_dir() and (item / '.saltbundle.yaml').exists():
            packages.append(item.name)

    return packages
