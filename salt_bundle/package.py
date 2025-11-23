"""Package management: packing and unpacking formulas."""

import re
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import load_package_meta
from .models.package_models import PackageMeta
from .utils.fs import collect_files
from .utils.hashing import calculate_sha256
from .utils.yaml import load_yaml


PACKAGE_NAME_PATTERN = re.compile(r'^[a-z0-9_-]+$')
SEMVER_PATTERN = re.compile(
    r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
    r'(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
    r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
    r'(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)


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
        FileNotFoundError: If .saltbundle.yaml doesn't exist
        ValueError: If package metadata is invalid
    """
    formula_dir = Path(formula_dir)
    if output_dir is None:
        output_dir = formula_dir
    else:
        output_dir = Path(output_dir)

    # Load and validate metadata
    meta = load_package_meta(formula_dir)

    if not validate_package_name(meta.name):
        raise ValueError(f"Invalid package name: {meta.name}")

    if not validate_semver(meta.version):
        raise ValueError(f"Invalid semver version: {meta.version}")

    # Check for at least one .sls file
    sls_files = list(formula_dir.glob('*.sls'))
    if not sls_files:
        raise ValueError("No .sls files found in formula directory")

    # Collect files to pack
    files = collect_files(formula_dir)

    # Ensure .saltbundle.yaml is included
    saltbundle_yaml = formula_dir / '.saltbundle.yaml'
    if saltbundle_yaml not in files:
        files.insert(0, saltbundle_yaml)

    # Create archive
    archive_name = f"{meta.name}-{meta.version}.tgz"
    archive_path = output_dir / archive_name

    with tarfile.open(archive_path, 'w:gz') as tar:
        for file_path in files:
            arcname = file_path.relative_to(formula_dir)
            tar.add(file_path, arcname=str(arcname))

    return archive_path


def unpack_formula(archive_path: Path | str, target_dir: Path | str) -> Path:
    """Unpack formula archive to target directory.

    Args:
        archive_path: Path to .tgz archive
        target_dir: Target directory to extract to

    Returns:
        Path to extracted formula directory

    Raises:
        FileNotFoundError: If archive doesn't exist
        tarfile.TarError: If archive is invalid
        ValueError: If archive doesn't contain .saltbundle.yaml
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

        tar.extractall(target_dir)

    # Verify .saltbundle.yaml exists
    saltbundle_yaml = target_dir / '.saltbundle.yaml'
    if not saltbundle_yaml.exists():
        raise ValueError("Archive doesn't contain .saltbundle.yaml")

    return target_dir


def get_package_info(archive_path: Path | str) -> PackageMeta:
    """Extract package metadata from archive without unpacking.

    Args:
        archive_path: Path to .tgz archive

    Returns:
        PackageMeta object

    Raises:
        FileNotFoundError: If archive doesn't exist
        ValueError: If .saltbundle.yaml not found in archive
    """
    archive_path = Path(archive_path)

    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    with tarfile.open(archive_path, 'r:gz') as tar:
        try:
            member = tar.getmember('.saltbundle.yaml')
            f = tar.extractfile(member)
            if f is None:
                raise ValueError(".saltbundle.yaml is a directory")

            import yaml
            data = yaml.safe_load(f)
            return PackageMeta(**data)
        except KeyError:
            raise ValueError("Archive doesn't contain .saltbundle.yaml")
