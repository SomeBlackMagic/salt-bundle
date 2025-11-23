"""Local filesystem release provider."""

import shutil
from pathlib import Path
from typing import Optional

from .base import ReleaseProvider
from ..models.index_models import Index
from ..utils.yaml import dump_yaml, load_yaml


class LocalReleaseProvider(ReleaseProvider):
    """Provider for storing packages in local filesystem.

    Structure:
        {pkg_storage_dir}/
        ├── index.yaml
        ├── {package-1}/
        │   ├── package-1-0.1.0.tgz
        │   ├── package-1-0.2.0.tgz
        │   └── package-1-0.2.3.tgz
        └── {package-2}/
            ├── package-2-0.1.0.tgz
            └── package-2-0.2.0.tgz
    """

    def __init__(self, pkg_storage_dir: Path | str):
        """Initialize local provider.

        Args:
            pkg_storage_dir: Directory where packages and index.yaml will be stored
        """
        self.pkg_storage_dir = Path(pkg_storage_dir)
        self.index_file = self.pkg_storage_dir / 'index.yaml'

    def initialize(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.pkg_storage_dir.mkdir(parents=True, exist_ok=True)

    def load_index(self) -> Optional[Index]:
        """Load existing index.yaml from local storage."""
        if not self.index_file.exists():
            return None

        try:
            data = load_yaml(self.index_file)
            return Index(**data)
        except Exception as e:
            print(f"Warning: Failed to load index from {self.index_file}: {e}")
            return None

    def save_index(self, index: Index) -> None:
        """Save index.yaml to local storage."""
        dump_yaml(index.model_dump(), self.index_file)

    def upload_package(self, package_name: str, version: str, archive_path: Path) -> str:
        """Copy package archive to local storage.

        Args:
            package_name: Name of the package
            version: Package version
            archive_path: Path to .tgz archive

        Returns:
            Relative URL path: {package-name}/{package-name}-{version}.tgz
        """
        # Create package directory
        package_dir = self.pkg_storage_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        # Copy archive
        archive_name = f"{package_name}-{version}.tgz"
        target_path = package_dir / archive_name
        shutil.copy2(archive_path, target_path)

        # Return relative URL
        return f"{package_name}/{archive_name}"

    def package_exists(self, package_name: str, version: str) -> bool:
        """Check if package version exists in local storage."""
        archive_name = f"{package_name}-{version}.tgz"
        package_path = self.pkg_storage_dir / package_name / archive_name
        return package_path.exists()
