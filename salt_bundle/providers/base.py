"""Base release provider interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..models.index_models import Index


class ReleaseProvider(ABC):
    """Abstract base class for release providers."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider (create directories, check credentials, etc)."""
        pass

    @abstractmethod
    def load_index(self) -> Optional[Index]:
        """Load existing index.yaml from provider storage.

        Returns:
            Index object if exists, None otherwise
        """
        pass

    @abstractmethod
    def save_index(self, index: Index) -> None:
        """Save index.yaml to provider storage.

        Args:
            index: Index object to save
        """
        pass

    @abstractmethod
    def upload_package(self, package_name: str, version: str, archive_path: Path) -> str:
        """Upload package archive to provider storage.

        Args:
            package_name: Name of the package
            version: Package version
            archive_path: Path to .tgz archive

        Returns:
            URL to download the package
        """
        pass

    @abstractmethod
    def package_exists(self, package_name: str, version: str) -> bool:
        """Check if package version already exists in provider storage.

        Args:
            package_name: Name of the package
            version: Package version

        Returns:
            True if package exists
        """
        pass
