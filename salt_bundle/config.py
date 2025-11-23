"""Configuration management for salt-bundle."""

import os
from pathlib import Path
from typing import Optional

from .models.config_models import ProjectConfig, UserConfig, RepositoryConfig
from .models.package_models import PackageMeta
from .utils.yaml import load_yaml, dump_yaml


def get_config_dir() -> Path:
    """Get user configuration directory (XDG compliant).

    Returns:
        Path to config directory (~/.config/salt-bundle)
    """
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        config_dir = Path(xdg_config) / 'salt-bundle'
    else:
        config_dir = Path.home() / '.config' / 'salt-bundle'

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """Get user cache directory (XDG compliant).

    Returns:
        Path to cache directory (~/.cache/salt-bundle)
    """
    xdg_cache = os.environ.get('XDG_CACHE_HOME')
    if xdg_cache:
        cache_dir = Path(xdg_cache) / 'salt-bundle'
    else:
        cache_dir = Path.home() / '.cache' / 'salt-bundle'

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def load_user_config() -> UserConfig:
    """Load user global configuration.

    Returns:
        UserConfig object (returns empty config if file doesn't exist)
    """
    config_file = get_config_dir() / 'config.yaml'

    if not config_file.exists():
        return UserConfig()

    data = load_yaml(config_file)
    return UserConfig(**data)


def save_user_config(config: UserConfig) -> None:
    """Save user global configuration.

    Args:
        config: UserConfig object to save
    """
    config_file = get_config_dir() / 'config.yaml'
    dump_yaml(config.model_dump(), config_file)


def add_user_repository(name: str, url: str) -> None:
    """Add repository to user configuration.

    Args:
        name: Repository name
        url: Repository URL

    Raises:
        ValueError: If repository with same name already exists
    """
    config = load_user_config()

    # Check if repository with same name exists
    for repo in config.repositories:
        if repo.name == name:
            raise ValueError(f"Repository '{name}' already exists")

    config.repositories.append(RepositoryConfig(name=name, url=url))
    save_user_config(config)


def add_project_repository(name: str, url: str, project_dir: Path | str = Path.cwd()) -> None:
    """Add repository to project configuration.

    Args:
        name: Repository name
        url: Repository URL
        project_dir: Project directory (defaults to current directory)

    Raises:
        ValueError: If repository with same name already exists
        FileNotFoundError: If .salt-dependencies.yaml doesn't exist
    """
    config = load_project_config(project_dir)

    # Check if repository with same name exists
    for repo in config.repositories:
        if repo.name == name:
            raise ValueError(f"Repository '{name}' already exists")

    config.repositories.append(RepositoryConfig(name=name, url=url))
    save_project_config(config, project_dir)


def load_project_config(project_dir: Path | str = Path.cwd()) -> ProjectConfig:
    """Load project configuration from .salt-dependencies.yaml.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        ProjectConfig object

    Raises:
        FileNotFoundError: If .salt-dependencies.yaml doesn't exist
    """
    config_file = Path(project_dir) / '.salt-dependencies.yaml'
    data = load_yaml(config_file)
    return ProjectConfig(**data)


def save_project_config(config: ProjectConfig, project_dir: Path | str = Path.cwd()) -> None:
    """Save project configuration to .salt-dependencies.yaml.

    Args:
        config: ProjectConfig object to save
        project_dir: Project directory (defaults to current directory)
    """
    config_file = Path(project_dir) / '.salt-dependencies.yaml'
    dump_yaml(config.model_dump(exclude_none=True), config_file)


def load_package_meta(package_dir: Path | str = Path.cwd()) -> PackageMeta:
    """Load package metadata from .saltbundle.yaml.

    Args:
        package_dir: Package directory (defaults to current directory)

    Returns:
        PackageMeta object

    Raises:
        FileNotFoundError: If .saltbundle.yaml doesn't exist
    """
    meta_file = Path(package_dir) / '.saltbundle.yaml'
    data = load_yaml(meta_file)
    return PackageMeta(**data)


def save_package_meta(meta: PackageMeta, package_dir: Path | str = Path.cwd()) -> None:
    """Save package metadata to .saltbundle.yaml.

    Args:
        meta: PackageMeta object to save
        package_dir: Package directory (defaults to current directory)
    """
    meta_file = Path(package_dir) / '.saltbundle.yaml'
    dump_yaml(meta.model_dump(exclude_none=True), meta_file)
