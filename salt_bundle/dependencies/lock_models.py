"""Pydantic models for Saltfile.lock."""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from ..packaging.naming import validate_package_name


class LockedDependency(BaseModel):
    """Single locked dependency with exact version and source."""
    version: str
    repository: str
    url: str
    digest: str  # format: "sha256:<hex>" or "path" for local path repos
    path: Optional[str] = None  # absolute path for type=path repositories
    type: Literal["formula", "extension"] = "formula"
    dependencies: dict[str, str] = Field(default_factory=dict)
    source_type: Literal["index", "path"] = "index"
    source_path: Optional[str] = None
    linked: bool = False

    @field_validator("dependencies")
    @classmethod
    def validate_dependency_names(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not validate_package_name(name) for name in value):
            raise ValueError("Locked dependency names must use vendor/package format")
        return value


class LockFile(BaseModel):
    """Complete lock file structure."""
    dependencies: dict[str, LockedDependency] = Field(default_factory=dict)

    @field_validator("dependencies")
    @classmethod
    def validate_package_names(cls, value: dict[str, LockedDependency]) -> dict[str, LockedDependency]:
        if any(not validate_package_name(name) for name in value):
            raise ValueError("Lock file package names must use vendor/package format")
        return value
