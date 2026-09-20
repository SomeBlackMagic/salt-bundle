"""Pydantic models for user-level configuration."""

from typing import Literal

from pydantic import BaseModel, Field


class RepositoryConfig(BaseModel):
    """Repository configuration entry."""
    name: str
    url: str
    type: Literal["remote", "path"] = "remote"


class UserConfig(BaseModel):
    """User global configuration from ~/.config/salt-bundle/config.yaml."""
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    allowed_repos: list[str] = Field(default_factory=list)  # optional security constraint
