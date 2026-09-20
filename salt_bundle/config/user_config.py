"""Configuration management for salt-bundle."""

import os
from pathlib import Path

from .models import UserConfig, RepositoryConfig
from ..utils.yaml import load_yaml, dump_yaml


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
