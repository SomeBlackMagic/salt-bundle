"""Pydantic models for EXTENSION package metadata."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .models import FormulaDependency, Maintainer
from .naming import validate_metadata_package_name


class PythonDependency(BaseModel):
    """Python dependency required by an extension."""

    name: str
    version: Optional[str] = None


class ConflictEntry(BaseModel):
    """Package that cannot be installed with an extension."""

    name: str
    reason: Optional[str] = None


class ExtensionMeta(BaseModel):
    """Complete package metadata from an EXTENSION file."""

    name: str
    version: str
    description: Optional[str] = None
    summary: Optional[str] = None
    minimum_version: Optional[str] = None
    maximum_version: Optional[str] = None
    python_requires: list[PythonDependency] = Field(default_factory=list)
    dependencies: list[FormulaDependency] = Field(default_factory=list)
    conflicts: list[ConflictEntry] = Field(default_factory=list)
    maintainers: list[Maintainer] = Field(default_factory=list)
    authors: list[Maintainer] = Field(default_factory=list)
    license: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    issues: Optional[str] = None

    @field_validator("minimum_version", "maximum_version", mode="before")
    @classmethod
    def normalize_salt_version(cls, value: object) -> object:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not validate_metadata_package_name(value):
            raise ValueError("Package name must use vendor/package format")
        return value

    @field_validator("dependencies", mode="before")
    @classmethod
    def parse_dependencies(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return [{"name": item} if isinstance(item, str) else item for item in value]
