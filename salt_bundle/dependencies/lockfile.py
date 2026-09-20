"""Lock file management for dependency resolution."""

from pathlib import Path

from .lock_models import LockFile, LockedDependency
from ..utils.yaml import dump_yaml, load_yaml


def load_lockfile(project_dir: Path | str = Path.cwd()) -> LockFile:
    """Load lock file from project directory.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        LockFile object (empty if file doesn't exist)

    Raises:
        FileNotFoundError: If Saltfile.lock doesn't exist
    """
    lock_path = Path(project_dir) / 'Saltfile.lock'
    
    if not lock_path.exists():
        return LockFile()

    data = load_yaml(lock_path)
    return LockFile(**data)


def save_lockfile(lockfile: LockFile, project_dir: Path | str = Path.cwd()) -> None:
    """Save Saltfile.lock to project directory.

    Args:
        lockfile: LockFile object to save
        project_dir: Project directory (defaults to current directory)
    """
    lock_path = Path(project_dir) / 'Saltfile.lock'
    dump_yaml(lockfile.model_dump(), lock_path)


def lockfile_exists(project_dir: Path | str = Path.cwd()) -> bool:
    """Check if lock file exists.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        True if Saltfile.lock exists
    """
    lock_path = Path(project_dir) / 'Saltfile.lock'
    return lock_path.exists()


def add_locked_dependency(
    lockfile: LockFile,
    name: str,
    version: str,
    repository: str,
    url: str,
    digest: str,
    path: str | None = None,
    package_type: str = "formula",
) -> None:
    """Add or update locked dependency.

    Args:
        lockfile: LockFile object to modify
        name: Package name
        version: Resolved version
        repository: Repository name
        url: Package URL
        digest: Package digest ("path" for local path repositories)
        path: Absolute local path for type=path repositories
        :param package_type:
    """
    lockfile.dependencies[name] = LockedDependency(
        version=version,
        repository=repository,
        url=url,
        digest=digest,
        path=path,
        type=package_type,
    )


def remove_locked_dependency(lockfile: LockFile, name: str) -> None:
    """Remove locked dependency.

    Args:
        lockfile: LockFile object to modify
        name: Package name to remove
    """
    if name in lockfile.dependencies:
        del lockfile.dependencies[name]
