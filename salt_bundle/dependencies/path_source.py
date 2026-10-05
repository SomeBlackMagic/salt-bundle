"""Resolve and materialize packages from local source directories."""

import shutil
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from ..packaging.types import detect_package_type, load_package_meta
from ..packaging.naming import canonicalize_package_name
from ..utils.fs import collect_files, load_ignore_patterns
from .index_models import Index, IndexEntry


def is_path_source(source: str) -> bool:
    """Return whether a dependency source denotes a local package directory."""
    return source.startswith("path://") or source.startswith("./") or source.startswith("../")


def resolve_source_path(source: str, project_dir: Path) -> Path:
    """Resolve a local path source relative to the project directory."""
    if source.startswith("path://"):
        raw_path = source.removeprefix("path://")
    else:
        raw_path = source
    if not raw_path:
        raise ValueError("Path source must include a directory")

    path = Path(raw_path)
    if not path.is_absolute():
        path = project_dir / path
    return path.resolve()


def validate_source_path(source_dir: Path) -> None:
    """Validate that a source directory contains exactly one package metadata file."""
    if not source_dir.exists():
        raise FileNotFoundError(f"source path not found: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"source path is not a directory: {source_dir}")
    try:
        detect_package_type(source_dir)
    except FileNotFoundError as exc:
        raise ValueError(f"no FORMULA or EXTENSION found at {source_dir}") from exc


def build_index_entry_from_path(source_dir: Path) -> IndexEntry:
    """Build an index-compatible entry from package metadata in ``source_dir``."""
    validate_source_path(source_dir)
    metadata = load_package_meta(source_dir)
    package_type = detect_package_type(source_dir)
    return IndexEntry(
        version=metadata.version,
        url=str(source_dir),
        digest=calculate_dir_digest(source_dir),
        created=datetime.now(),
        keywords=getattr(metadata, "keywords", []),
        maintainers=metadata.maintainers,
        sources=[metadata.source] if metadata.source else [],
        dependencies=metadata.dependencies,
        type=package_type,
    )


def build_index_from_directory(repository_dir: Path) -> Index:
    """Build a virtual package index by scanning direct repository children."""
    if not repository_dir.exists():
        raise FileNotFoundError(f"source path not found: {repository_dir}")
    if not repository_dir.is_dir():
        raise NotADirectoryError(f"source path is not a directory: {repository_dir}")

    packages: dict[str, list[IndexEntry]] = {}
    for candidate_dir in sorted(repository_dir.iterdir()):
        if not candidate_dir.is_dir():
            continue
        try:
            metadata = load_package_meta(candidate_dir)
            entry = build_index_entry_from_path(candidate_dir)
        except (FileNotFoundError, NotADirectoryError, ValueError):
            continue
        packages.setdefault(canonicalize_package_name(metadata.name).full_name, []).append(entry)
    return Index(generated=datetime.now(), packages=packages)


def _materialized_files(source_dir: Path) -> list[tuple[Path, Path]]:
    """Return destination-relative source files using archive materialization rules."""
    metadata_file = source_dir / ("FORMULA" if detect_package_type(source_dir) == "formula" else "EXTENSION")
    patterns = load_ignore_patterns(source_dir)
    files = [(path.relative_to(source_dir), path) for path in collect_files(source_dir, patterns)]
    if not any(relative == Path(metadata_file.name) for relative, _ in files):
        files.append((Path(metadata_file.name), metadata_file))
    return sorted(files, key=lambda item: item[0].as_posix())


def calculate_dir_digest(source_dir: Path) -> str:
    """Calculate the activation-compatible digest of materialized package contents."""
    digest = sha256()
    for relative_path, file_path in _materialized_files(source_dir):
        digest.update(relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _remove_existing(target_dir: Path) -> None:
    if target_dir.is_symlink() or target_dir.is_file():
        target_dir.unlink()
    elif target_dir.exists():
        shutil.rmtree(target_dir)


def install_from_path_snapshot(source_dir: Path, package_name: str, vendor_dir: Path) -> Path:
    """Copy a local package using the same file layout as archive installation."""
    validate_source_path(source_dir)
    actual_name = canonicalize_package_name(load_package_meta(source_dir).name).full_name
    if package_name != actual_name:
        raise ValueError(
            f"Package name mismatch: expected '{package_name}', but FORMULA declares '{actual_name}'"
        )
    target_dir = vendor_dir / package_name
    _remove_existing(target_dir)
    target_dir.mkdir(parents=True)
    for relative_path, file_path in _materialized_files(source_dir):
        destination = target_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination)
    return target_dir


def install_from_path_link(source_dir: Path, package_name: str, vendor_dir: Path) -> Path:
    """Link a local package directory into the vendor directory."""
    validate_source_path(source_dir)
    metadata = load_package_meta(source_dir)
    actual_name = canonicalize_package_name(metadata.name).full_name
    if package_name != actual_name:
        raise ValueError(
            f"Package name mismatch: expected '{package_name}', but FORMULA declares '{actual_name}'"
        )
    target_dir = vendor_dir / package_name
    _remove_existing(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    target_dir.symlink_to(source_dir, target_is_directory=True)
    return target_dir
