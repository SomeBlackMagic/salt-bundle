"""Pydantic models for project configuration (.saltbundle.yaml for project)."""

from typing import Optional
from pydantic import BaseModel, Field


class RepositoryConfig(BaseModel):
    """Repository configuration entry."""
    name: str
    url: str


class ProjectConfig(BaseModel):
    """Project configuration from .saltbundle.yaml."""
    project: str
    version: Optional[str] = None
    vendor_dir: str = "vendor"
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    dependencies: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Package dependencies with version constraints. "
            "Supports two formats:\n"
            "  1. 'package_name': 'version' - searches all repositories\n"
            "  2. 'repo_name/package_name': 'version' - searches specific repository\n"
            "Example:\n"
            "  nginx: '^1.0.0'  # searches all repos\n"
            "  main/mysql: '2.3.1'  # only from 'main' repo"
        )
    )


class UserConfig(BaseModel):
    """User global configuration from ~/.config/salt-bundle/config.yaml."""
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    allowed_repos: list[str] = Field(default_factory=list)  # optional security constraint
