"""Pydantic models for Saltfile.lock."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class LockedDependency(BaseModel):
    """Single locked dependency with exact version and source."""
    version: str
    repository: str
    url: str
    digest: str  # format: "sha256:<hex>" or "path" for local path repos
    path: Optional[str] = None  # absolute path for type=path repositories
    type: Literal["formula", "extension"] = "formula"


class LockFile(BaseModel):
    """Complete lock file structure."""
    dependencies: dict[str, LockedDependency] = Field(default_factory=dict)
