"""GitHub integration for salt-bundle."""

import os
from pathlib import Path
from typing import Optional

from github import Github, GithubException


class GitHubReleaser:
    """Handle GitHub releases for salt-bundle packages."""

    def __init__(self, token: Optional[str] = None, repository: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            token: GitHub token (defaults to GITHUB_TOKEN env var)
            repository: Repository in format 'owner/repo' (defaults to GITHUB_REPOSITORY env var)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repository_name = repository or os.getenv('GITHUB_REPOSITORY')

        if not self.token:
            raise ValueError("GitHub token not provided. Set GITHUB_TOKEN environment variable or pass token parameter")

        if not self.repository_name:
            raise ValueError("GitHub repository not provided. Set GITHUB_REPOSITORY environment variable or pass repository parameter")

        self.client = Github(self.token)
        self.repo = self.client.get_repo(self.repository_name)

    def create_release(self, tag_name: str, name: str, body: str = "") -> str:
        """Create a GitHub release.

        Args:
            tag_name: Git tag name (e.g., 'apache-1.0.0')
            name: Release name
            body: Release description

        Returns:
            Release HTML URL
        """
        try:
            release = self.repo.create_git_release(
                tag=tag_name,
                name=name,
                message=body,
                draft=False,
                prerelease=False
            )
            return release.html_url
        except GithubException as e:
            if e.status == 422 and 'already_exists' in str(e.data):
                # Tag already exists, get existing release
                release = self.repo.get_release(tag_name)
                return release.html_url
            raise

    def upload_asset(self, tag_name: str, file_path: Path, label: Optional[str] = None) -> str:
        """Upload asset to existing release.

        Args:
            tag_name: Git tag name
            file_path: Path to file to upload
            label: Optional label for the asset

        Returns:
            Asset download URL
        """
        release = self.repo.get_release(tag_name)

        # Check if asset already exists
        for asset in release.get_assets():
            if asset.name == file_path.name:
                # Delete old asset
                asset.delete_asset()
                break

        # Upload new asset
        asset = release.upload_asset(
            str(file_path),
            label=label or file_path.name,
            content_type='application/gzip'
        )

        return asset.browser_download_url

    def create_release_with_asset(
        self,
        package_name: str,
        version: str,
        archive_path: Path,
        description: str = ""
    ) -> tuple[str, str]:
        """Create release and upload package archive.

        Args:
            package_name: Package name
            version: Package version
            archive_path: Path to .tgz archive
            description: Package description

        Returns:
            Tuple of (release_url, asset_download_url)
        """
        tag_name = f"{package_name}-{version}"
        release_name = f"{package_name} {version}"

        # Create release
        release_url = self.create_release(
            tag_name=tag_name,
            name=release_name,
            body=description
        )

        # Upload asset
        asset_url = self.upload_asset(tag_name, archive_path)

        return release_url, asset_url

    def get_release_asset_url(self, package_name: str, version: str, filename: str) -> str:
        """Get download URL for release asset.

        Args:
            package_name: Package name
            version: Package version
            filename: Asset filename

        Returns:
            Asset download URL
        """
        tag_name = f"{package_name}-{version}"
        release = self.repo.get_release(tag_name)

        for asset in release.get_assets():
            if asset.name == filename:
                return asset.browser_download_url

        raise ValueError(f"Asset {filename} not found in release {tag_name}")

    def release_exists(self, package_name: str, version: str) -> bool:
        """Check if release already exists.

        Args:
            package_name: Package name
            version: Package version

        Returns:
            True if release exists
        """
        tag_name = f"{package_name}-{version}"
        try:
            self.repo.get_release(tag_name)
            return True
        except GithubException:
            return False
