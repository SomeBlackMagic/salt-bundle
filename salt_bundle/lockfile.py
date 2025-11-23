"""Lock file management for dependency resolution."""

from pathlib import Path

from .models.lock_models import LockFile, LockedDependency
from .utils.yaml import dump_yaml, load_yaml


def load_lockfile(project_dir: Path | str = Path.cwd()) -> LockFile:
    """Load lock file from project directory.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        LockFile object (empty if file doesn't exist)

    Raises:
        FileNotFoundError: If .salt-dependencies.lock doesn't exist
    """
    lock_path = Path(project_dir) / '.salt-dependencies.lock'
    
    if not lock_path.exists():
        return LockFile()

    data = load_yaml(lock_path)
    return LockFile(**data)


def save_lockfile(lockfile: LockFile, project_dir: Path | str = Path.cwd()) -> None:
    """Save lock file to project directory.

    Args:
        lockfile: LockFile object to save
        project_dir: Project directory (defaults to current directory)
    """
    lock_path = Path(project_dir) / '.salt-dependencies.lock'
    dump_yaml(lockfile.model_dump(), lock_path)


def lockfile_exists(project_dir: Path | str = Path.cwd()) -> bool:
    """Check if lock file exists.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        True if .salt-dependencies.lock exists
    """
    lock_path = Path(project_dir) / '.salt-dependencies.lock'
    return lock_path.exists()


def add_locked_dependency(
    lockfile: LockFile,
    name: str,
    version: str,
    repository: str,
    url: str,
    digest: str
) -> None:
    """Add or update locked dependency.

    Args:
        lockfile: LockFile object to modify
        name: Package name
        version: Resolved version
        repository: Repository name
        url: Package URL
        digest: Package digest
    """
    lockfile.dependencies[name] = LockedDependency(
        version=version,
        repository=repository,
        url=url,
        digest=digest
    )


def remove_locked_dependency(lockfile: LockFile, name: str) -> None:
    """Remove locked dependency.

    Args:
        lockfile: LockFile object to modify
        name: Package name to remove
    """
    if name in lockfile.dependencies:
        del lockfile.dependencies[name]
