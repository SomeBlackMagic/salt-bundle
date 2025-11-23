"""GitHub release provider."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base import ReleaseProvider
from ..github import GitHubReleaser
from ..models.index_models import Index
from ..utils.yaml import dump_yaml, load_yaml


class GitHubReleaseProvider(ReleaseProvider):
    """Provider for storing packages as GitHub releases with index in gh-pages branch.

    - Packages are uploaded as release assets
    - index.yaml is stored in a separate branch (default: gh-pages)
    - The index branch contains ONLY index.yaml file
    """

    def __init__(
        self,
        token: Optional[str] = None,
        repository: Optional[str] = None,
        index_branch: str = 'gh-pages'
    ):
        """Initialize GitHub provider.

        Args:
            token: GitHub token (defaults to GITHUB_TOKEN env var)
            repository: Repository in format 'owner/repo' (defaults to GITHUB_REPOSITORY env var)
            index_branch: Git branch name for index.yaml (default: gh-pages)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repository_name = repository or os.getenv('GITHUB_REPOSITORY')
        self.index_branch = index_branch

        if not self.token:
            raise ValueError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable or pass token parameter"
            )

        if not self.repository_name:
            raise ValueError(
                "GitHub repository not provided. Set GITHUB_REPOSITORY environment variable or pass repository parameter"
            )

        self.gh_client = GitHubReleaser(token=self.token, repository=self.repository_name)
        self._git_root: Optional[Path] = None

    def initialize(self) -> None:
        """Verify GitHub credentials and repository access."""
        # Test connection by accessing repository
        try:
            _ = self.gh_client.repo.name
        except Exception as e:
            raise RuntimeError(f"Failed to access GitHub repository {self.repository_name}: {e}")

    def _find_git_root(self) -> Optional[Path]:
        """Find git repository root."""
        if self._git_root:
            return self._git_root

        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            self._git_root = Path(result.stdout.strip())
            return self._git_root
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def load_index(self) -> Optional[Index]:
        """Load index.yaml from GitHub branch."""
        git_root = self._find_git_root()
        if not git_root:
            # Try to fetch from GitHub API
            return self._load_index_from_github_api()

        try:
            # Fetch the latest version of the index branch from remote
            result = subprocess.run(
                ['git', 'fetch', 'origin', f'{self.index_branch}:{self.index_branch}'],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=False
            )

            # If fetch failed, try to fetch without local branch
            if result.returncode != 0:
                subprocess.run(
                    ['git', 'fetch', 'origin', self.index_branch],
                    cwd=git_root,
                    capture_output=True,
                    check=False
                )

            # Try to load from git branch (use origin/branch if local doesn't exist)
            for ref in [f'{self.index_branch}:index.yaml', f'origin/{self.index_branch}:index.yaml']:
                result = subprocess.run(
                    ['git', 'show', ref],
                    cwd=git_root,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    import yaml
                    data = yaml.safe_load(result.stdout)
                    print(f"Loaded index from {ref}")
                    return Index(**data)

            # Branch doesn't exist or no index.yaml
            print(f"No existing index found in {self.index_branch} branch")
            return None

        except Exception as e:
            print(f"Warning: Failed to load index from {self.index_branch} branch: {e}")
            # Fallback to API
            return self._load_index_from_github_api()

    def _load_index_from_github_api(self) -> Optional[Index]:
        """Load index.yaml using GitHub API."""
        try:
            contents = self.gh_client.repo.get_contents('index.yaml', ref=self.index_branch)
            if isinstance(contents, list):
                return None

            import yaml
            data = yaml.safe_load(contents.decoded_content)
            return Index(**data)
        except Exception:
            return None

    def save_index(self, index: Index) -> None:
        """Save index.yaml to GitHub branch.

        Commits and pushes index.yaml to the configured branch.
        The branch will contain ONLY index.yaml file.
        """
        git_root = self._find_git_root()
        if not git_root:
            raise RuntimeError("Not in a git repository. Cannot commit index.yaml to branch.")

        # Log what we're about to save
        total_versions = sum(len(versions) for versions in index.packages.values())
        print(f"Saving index with {len(index.packages)} packages, {total_versions} total versions:")
        for pkg_name, versions in index.packages.items():
            print(f"  - {pkg_name}: {len(versions)} version(s)")

        # Create temporary file for index
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_index = Path(f.name)
            dump_yaml(index.model_dump(), temp_index)

        try:
            self._commit_index_to_branch(temp_index, git_root)
        finally:
            # Clean up temp file
            if temp_index.exists():
                temp_index.unlink()

    def _commit_index_to_branch(self, index_file: Path, repo_dir: Path) -> None:
        """Commit index.yaml to separate orphan branch."""
        # Save current branch
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = result.stdout.strip()

        try:
            # Check if branch exists remotely
            result = subprocess.run(
                ['git', 'ls-remote', '--heads', 'origin', self.index_branch],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=False
            )
            branch_exists_remote = bool(result.stdout.strip())

            # Fetch remote branch if exists
            if branch_exists_remote:
                subprocess.run(
                    ['git', 'fetch', 'origin', f'{self.index_branch}:{self.index_branch}'],
                    cwd=repo_dir,
                    capture_output=True,
                    check=False
                )

            # Check if branch exists locally
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', self.index_branch],
                cwd=repo_dir,
                capture_output=True,
                check=False
            )
            branch_exists = result.returncode == 0

            # Checkout or create branch
            if branch_exists:
                subprocess.run(
                    ['git', 'checkout', self.index_branch],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
            else:
                # Create orphan branch (no history)
                subprocess.run(
                    ['git', 'checkout', '--orphan', self.index_branch],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Remove all files from staging
                subprocess.run(
                    ['git', 'rm', '-rf', '.'],
                    cwd=repo_dir,
                    capture_output=True,
                    check=False
                )

            # Copy index.yaml to repo root
            import shutil
            target_index = repo_dir / 'index.yaml'
            shutil.copy2(index_file, target_index)

            # Add index.yaml
            subprocess.run(
                ['git', 'add', 'index.yaml'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            )

            # Check if there are changes to commit
            result = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                cwd=repo_dir,
                capture_output=True,
                check=False
            )

            if result.returncode != 0:
                # Commit changes
                subprocess.run(
                    ['git', 'commit', '-m', 'Update package index'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Push to remote
                subprocess.run(
                    ['git', 'push', 'origin', self.index_branch],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"Index committed and pushed to {self.index_branch} branch")
            else:
                print(f"No changes to index.yaml")

        finally:
            # Return to original branch
            subprocess.run(
                ['git', 'checkout', current_branch],
                cwd=repo_dir,
                capture_output=True,
                check=False
            )

    def upload_package(self, package_name: str, version: str, archive_path: Path) -> str:
        """Upload package as GitHub release asset.

        Creates a release with tag {package-name}-{version} and uploads the archive.

        Args:
            package_name: Name of the package
            version: Package version
            archive_path: Path to .tgz archive

        Returns:
            Asset download URL
        """
        description = f"{package_name} version {version}"
        _, asset_url = self.gh_client.create_release_with_asset(
            package_name,
            version,
            archive_path,
            description
        )
        return asset_url

    def package_exists(self, package_name: str, version: str) -> bool:
        """Check if release exists on GitHub."""
        return self.gh_client.release_exists(package_name, version)
