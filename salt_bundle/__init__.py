"""salt-bundle - Salt package manager."""

from importlib.metadata import version

__version__ = version("salt-bundle")

from . import (
    config,
    lockfile,
    package,
    repository,
    resolver,
    vendor,
)

__all__ = [
    "config",
    "lockfile",
    "package",
    "repository",
    "resolver",
    "vendor",
]