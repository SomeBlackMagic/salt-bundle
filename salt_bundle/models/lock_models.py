"""Pydantic models for lock file (.salt-dependencies.lock)."""

from pydantic import BaseModel, Field


class LockedDependency(BaseModel):
    """Single locked dependency with exact version and source."""
    version: str
    repository: str
    url: str
    digest: str  # format: "sha256:<hex>"


class LockFile(BaseModel):
    """Complete lock file structure."""
    dependencies: dict[str, LockedDependency] = Field(default_factory=dict)
