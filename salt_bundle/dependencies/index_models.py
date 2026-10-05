"""Pydantic models for repository index (index.yaml)."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from ..packaging.models import Maintainer, FormulaDependency
from ..packaging.naming import validate_package_name


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

    @field_validator("packages")
    @classmethod
    def validate_package_names(cls, value: dict[str, list[IndexEntry]]) -> dict[str, list[IndexEntry]]:
        invalid_names = [name for name in value if not validate_package_name(name)]
        if invalid_names:
            raise ValueError("Index package names must use vendor/package format")
        return value
