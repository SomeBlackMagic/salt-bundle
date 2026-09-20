"""Package management: packing and unpacking formulas."""

import re
import tarfile
from pathlib import Path
from typing import Optional

from .extensions import ExtensionMeta
from .metadata import load_formula_meta, load_extension_meta
from .models import PackageMeta
from .types import get_package_info_from_archive, detect_package_type
from ..utils.fs import collect_files, load_ignore_patterns

PACKAGE_NAME_PATTERN = re.compile(r'^[a-z0-9_-]+$')
SEMVER_PATTERN = re.compile(
    r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
    r'(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
    r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
    r'(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)
EXTENSION_DIRECTORY_NAMES = frozenset({
    "_auth", "_beacons", "_cache", "_clouds", "_engines", "_executors",
    "_fileserver", "_grains", "_log_handlers", "_matchers", "_metaproxy",
    "_modules", "_netapi", "_output", "_pillar", "_pkgdb", "_pkgfiles",
    "_proxy", "_queues", "_renderers", "_returners", "_roster", "_runners",
    "_sdb", "_serializers", "_states", "_thorium", "_tokens", "_tops",
    "_utils", "_wheel", "_wrapper",
})


def validate_package_name(name: str) -> bool:
    """Validate package name format.

    Args:
        name: Package name

    Returns:
        True if valid, False otherwise
    """
    return bool(PACKAGE_NAME_PATTERN.match(name))


def validate_semver(version: str) -> bool:
    """Validate semantic version format.

    Args:
        version: Version string

    Returns:
        True if valid semver, False otherwise
    """
    return bool(SEMVER_PATTERN.match(version))


def pack_formula(
    formula_dir: Path | str = Path.cwd(),
    output_dir: Optional[Path | str] = None
) -> Path:
    """Pack formula into tar.gz archive.

    Args:
        formula_dir: Formula directory (defaults to current directory)
        output_dir: Output directory (defaults to formula_dir)

    Returns:
        Path to created archive

    Raises:
        FileNotFoundError: If FORMULA doesn't exist
        ValueError: If package metadata is invalid
    """
    formula_dir = Path(formula_dir)
    if output_dir is None:
        output_dir = formula_dir
    else:
        output_dir = Path(output_dir)

    # Load and validate metadata
    meta = load_formula_meta(formula_dir)

    if not validate_package_name(meta.name):
        raise ValueError(f"Invalid package name: {meta.name}")

    if not validate_semver(meta.version):
        raise ValueError(f"Invalid semver version: {meta.version}")

    if meta.top_level_dir:
        source_dir = (formula_dir / meta.top_level_dir).resolve()
        formula_dir_resolved = formula_dir.resolve()
        if not source_dir.is_relative_to(formula_dir_resolved):
            raise ValueError(f"top_level_dir escapes formula_dir: {meta.top_level_dir}")
        if not source_dir.is_dir():
            raise FileNotFoundError(f"top_level_dir does not exist: {source_dir}")
    else:
        source_dir = formula_dir

    # Check for at least one .sls file
    sls_files = list(source_dir.glob('*.sls'))
    if not sls_files:
        raise ValueError(f"No .sls files found in source directory: {source_dir}")

    # Collect files to pack
    patterns = load_ignore_patterns(formula_dir)
    files = collect_files(source_dir, patterns)
    formula_file = formula_dir / 'FORMULA'

    # Create archive
    archive_name = f"{meta.name}-{meta.version}.tgz"
    archive_path = output_dir / archive_name

    with tarfile.open(archive_path, 'w:gz') as tar:
        for file_path in files:
            arcname = file_path.relative_to(source_dir)
            if arcname == Path('FORMULA') and file_path != formula_file:
                continue
            tar.add(file_path, arcname=str(arcname))
        if formula_file not in files:
            tar.add(formula_file, arcname='FORMULA')

    return archive_path


def pack_extension(
    extension_dir: Path | str = Path.cwd(),
    output_dir: Optional[Path | str] = None,
) -> Path:
    """Pack an EXTENSION package into a tar.gz archive."""
    extension_dir = Path(extension_dir)
    output_path = extension_dir if output_dir is None else Path(output_dir)
    meta = load_extension_meta(extension_dir)
    if not validate_package_name(meta.name):
        raise ValueError(f"Invalid package name: {meta.name}")
    if not validate_semver(meta.version):
        raise ValueError(f"Invalid semver version: {meta.version}")

    module_directories = [
        path for path in extension_dir.iterdir()
        if path.is_dir() and path.name in EXTENSION_DIRECTORY_NAMES
    ]
    if not module_directories:
        raise ValueError("Extension must contain at least one supported Salt module directory")

    patterns = load_ignore_patterns(extension_dir)
    files = collect_files(extension_dir, patterns)
    metadata_file = extension_dir / "EXTENSION"
    archive_path = output_path / f"{meta.name}-{meta.version}.tgz"
    with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in files:
            if file_path == metadata_file:
                continue
            tar.add(file_path, arcname=str(file_path.relative_to(extension_dir)))
        tar.add(metadata_file, arcname="EXTENSION")
    return archive_path


def pack_package(
    package_dir: Path | str = Path.cwd(),
    output_dir: Optional[Path | str] = None,
) -> Path:
    """Pack a formula or extension based on its metadata file."""
    if detect_package_type(package_dir) == "formula":
        return pack_formula(package_dir, output_dir)
    return pack_extension(package_dir, output_dir)


def unpack_package(archive_path: Path | str, target_dir: Path | str) -> Path:
    """Unpack formula archive to target directory.

    Args:
        archive_path: Path to .tgz archive
        target_dir: Target directory to extract to

    Returns:
        Path to extracted formula directory

    Raises:
        FileNotFoundError: If archive doesn't exist
        tarfile.TarError: If archive is invalid
        ValueError: If archive doesn't contain FORMULA
    """
    archive_path = Path(archive_path)
    target_dir = Path(target_dir)

    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    target_dir.mkdir(parents=True, exist_ok=True)

    # Extract archive
    with tarfile.open(archive_path, 'r:gz') as tar:
        # Security check: ensure no path traversal
        for member in tar.getmembers():
            if member.name.startswith('/') or '..' in member.name:
                raise ValueError(f"Invalid path in archive: {member.name}")

        tar.extractall(target_dir, filter="data")

    detect_package_type(target_dir)

    return target_dir


def get_package_info(archive_path: Path | str) -> PackageMeta | ExtensionMeta:
    """Extract package metadata from archive without unpacking.

    Args:
        archive_path: Path to .tgz archive

    Returns:
        PackageMeta object

    Raises:
        FileNotFoundError: If archive doesn't exist
        ValueError: If FORMULA not found in archive
    """
    return get_package_info_from_archive(archive_path)


unpack_formula = unpack_package
