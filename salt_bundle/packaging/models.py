"""Pydantic models for package metadata (FORMULA file)."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Maintainer(BaseModel):
    """Package maintainer or author information."""
    name: str
    email: Optional[str] = None
    github: Optional[str] = None


class FormulaDependency(BaseModel):
    """Package dependency with optional version constraint.

    Supports two YAML forms:
      - Plain string: ``nginx``  (resolves to latest)
      - Mapping: ``{name: mysql, version: ^2.0.0}``
    """
    name: str
    version: Optional[str] = None  # semver range; None → use latest
    url: Optional[str] = None


class PackageMeta(BaseModel):
    """Complete package metadata from FORMULA file."""
    name: str
    version: str
    os: Optional[str] = None
    os_family: Optional[str] = None
    minimum_version: Optional[str] = None
    maximum_version: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    top_level_dir: Optional[str] = None
    dependencies: list[FormulaDependency] = Field(default_factory=list)
    filtered_args: list[str] = Field(default_factory=list)
    maintainers: list[Maintainer] = Field(default_factory=list)
    authors: list[Maintainer] = Field(default_factory=list)
    license: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    issues: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)

    @field_validator('dependencies', mode='before')
    @classmethod
    def parse_dependencies(cls, v: object) -> list:
        if not isinstance(v, list):
            return v
        result = []
        for item in v:
            if isinstance(item, str):
                result.append({'name': item})
            else:
                result.append(item)
        return result

    @field_validator('top_level_dir', mode='before')
    @classmethod
    def validate_top_level_dir(cls, value: object) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, (str, Path)):
            return value

        top_level_dir = str(value).strip()
        if not top_level_dir or top_level_dir == '.':
            return None

        path = Path(top_level_dir)
        if path.is_absolute():
            raise ValueError("top_level_dir must be a relative path")
        if '..' in path.parts:
            raise ValueError("top_level_dir must not contain '..' components")

        return path.as_posix()
