"""Package type detection and metadata loading."""

import tarfile
from pathlib import Path
from typing import Literal

import yaml

from .extensions import ExtensionMeta
from .models import PackageMeta
from ..utils.yaml import load_yaml

PackageType = Literal["formula", "extension"]
PackageMetadata = PackageMeta | ExtensionMeta


def detect_package_type(path: Path | str) -> PackageType:
    """Detect a package type from its mutually exclusive metadata file."""
    package_dir = Path(path)
    has_formula = (package_dir / "FORMULA").is_file()
    has_extension = (package_dir / "EXTENSION").is_file()

    if has_formula and has_extension:
        raise ValueError("Package contains both FORMULA and EXTENSION metadata files")
    if has_formula:
        return "formula"
    if has_extension:
        return "extension"
    raise FileNotFoundError(f"No FORMULA or EXTENSION file found in {package_dir}")


def load_package_meta(path: Path | str) -> PackageMetadata:
    """Load metadata matching the type of a package directory."""
    package_dir = Path(path)
    package_type = detect_package_type(package_dir)
    metadata_path = package_dir / ("FORMULA" if package_type == "formula" else "EXTENSION")
    metadata = load_yaml(metadata_path)
    if package_type == "formula":
        return PackageMeta(**metadata)
    return ExtensionMeta(**metadata)


def get_package_info_from_archive(archive: Path | str) -> PackageMetadata:
    """Read package metadata from an archive without extracting it."""
    archive_path = Path(archive)
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    with tarfile.open(archive_path, "r:gz") as tar:
        members = {member.name: member for member in tar.getmembers()}
        has_formula = "FORMULA" in members
        has_extension = "EXTENSION" in members
        if has_formula and has_extension:
            raise ValueError("Archive contains both FORMULA and EXTENSION metadata files")
        if not has_formula and not has_extension:
            raise ValueError("Archive contains neither FORMULA nor EXTENSION")

        member_name = "FORMULA" if has_formula else "EXTENSION"
        stream = tar.extractfile(members[member_name])
        if stream is None:
            raise ValueError(f"{member_name} is a directory")
        metadata = yaml.safe_load(stream) or {}
        if has_formula:
            return PackageMeta(**metadata)
        return ExtensionMeta(**metadata)
