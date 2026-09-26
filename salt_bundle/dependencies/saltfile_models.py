"""Pydantic models for the Saltfile project manifest."""

from typing import Optional

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    """Runtime paths and execution defaults for a Salt project."""

    top_bundle_file: str = "top_bundle.sls"
    cache_dir: str = ".salt-bundle/runtime"
    max_workers: int = Field(default=4, ge=1)
    require_bundle_top: bool = False


class SaltfileDependency(BaseModel):
    """A package dependency resolved through an index.yaml repository."""

    name: str
    version: Optional[str] = None
    source: Optional[str] = None


class SaltfileConfig(BaseModel):
    """Project dependencies declared in Saltfile."""

    dependencies: list[SaltfileDependency] = Field(default_factory=list)
    vendor_dir: str = "vendor"
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
