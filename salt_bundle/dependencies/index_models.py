"""Pydantic models for repository index (index.yaml)."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

from ..packaging.models import Maintainer, FormulaDependency


class IndexEntry(BaseModel):
    """Single version entry in repository index."""
    version: str
    url: str
    digest: str  # format: "sha256:<hex>"
    created: Optional[datetime] = None
    keywords: list[str] = Field(default_factory=list)
    maintainers: list[Maintainer] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    dependencies: list[FormulaDependency] = Field(default_factory=list)
    type: Literal["formula", "extension"] = "formula"


class Index(BaseModel):
    """Complete repository index structure."""
    apiVersion: str = "v1"
    generated: datetime
    packages: dict[str, list[IndexEntry]] = Field(default_factory=dict)
