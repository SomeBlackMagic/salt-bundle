"""Pydantic models for package metadata (.saltbundle.yaml for formula)."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Maintainer(BaseModel):
    """Package maintainer information."""
    name: str
    email: Optional[str] = None


class SaltCompatibility(BaseModel):
    """Salt version compatibility constraints."""
    min_version: Optional[str] = None
    max_version: Optional[str] = None


class PackageDependency(BaseModel):
    """Package dependency with version constraint."""
    name: str
    version: str  # semver range like "^1.0", "~1.2.3", ">=1.0,<2.0"


class PackageEntry(BaseModel):
    """Entry points configuration for package."""
    states_root: str = "."
    pillar_root: Optional[str] = None
    modules: list[str] = Field(default_factory=list)


class PackageMeta(BaseModel):
    """Complete package metadata from .saltbundle.yaml."""
    name: str
    version: str
    formula_path: Optional[str] = None
    description: Optional[str] = None
    maintainers: list[Maintainer] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    salt: Optional[SaltCompatibility] = None
    dependencies: list[PackageDependency] = Field(default_factory=list)
    entry: Optional[PackageEntry] = None

    @field_validator('formula_path', mode='before')
    @classmethod
    def validate_formula_path(cls, value: object) -> Optional[str]:
        """Validate and normalize the optional formula source path."""
        if value is None:
            return None
        if not isinstance(value, (str, Path)):
            return value

        formula_path = str(value).strip()
        if not formula_path or formula_path == '.':
            return None

        path = Path(formula_path)
        if path.is_absolute():
            raise ValueError("formula_path must be a relative path")
        if '..' in path.parts:
            raise ValueError("formula_path must not contain '..' components")

        return path.as_posix()
