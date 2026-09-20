"""Pydantic models for the Saltfile project manifest."""

from typing import Optional

from pydantic import BaseModel, Field


class SaltfileDependency(BaseModel):
    """A package dependency resolved through an index.yaml repository."""

    name: str
    version: Optional[str] = None
    source: Optional[str] = None


class SaltfileConfig(BaseModel):
    """Project dependencies declared in Saltfile."""

    dependencies: list[SaltfileDependency] = Field(default_factory=list)
    vendor_dir: str = "vendor"
