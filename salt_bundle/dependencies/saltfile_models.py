"""Pydantic models for the Saltfile project manifest."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from ..config.models import RepositoryConfig
from ..packaging.naming import validate_package_name


class RuntimeConfig(BaseModel):
    """Runtime paths and execution defaults for a Salt project."""

    top_bundle_file: str = "salt/top_bundle.sls"
    cache_dir: str = ".salt-bundle/runtime"
    max_workers: int = Field(default=4, ge=1)
    require_bundle_top: bool = False


class SaltfileDependency(BaseModel):
    """A package dependency resolved through a repository or local path."""

    name: str
    version: Optional[str] = None
    source: Optional[str] = None
    link: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not validate_package_name(value):
            raise ValueError("Dependency name must use vendor/package format")
        return value


class SaltfileConfig(BaseModel):
    """Project dependencies declared in Saltfile."""

    repositories: list[RepositoryConfig] = Field(default_factory=list)
    dependencies: list[SaltfileDependency] = Field(default_factory=list)
    vendor_dir: str = "vendor"
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
