import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from salt_bundle.dependencies.index_models import Index
from salt_bundle.storage.github import GitHubReleaser
from salt_bundle.storage.providers.github_provider import GitHubReleaseProvider


class TestGitHubStorage(unittest.TestCase):
    @patch("salt_bundle.storage.github.Github")
    def test_github_releaser_manages_release_assets(self, github_class: MagicMock) -> None:
        repository = github_class.return_value.get_repo.return_value
        release = repository.create_git_release.return_value
        release.html_url = "https://example.test/release"
        existing_asset = MagicMock(name="existing")
        existing_asset.name = "package.tgz"
        existing_asset.browser_download_url = "https://example.test/package.tgz"
        uploaded_asset = MagicMock()
        uploaded_asset.browser_download_url = "https://example.test/package.tgz"
        release.get_assets.return_value = [existing_asset]
        release.upload_asset.return_value = uploaded_asset
        repository.get_release.return_value = release

        releaser = GitHubReleaser(token="token", repository="owner/repository")
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "package.tgz"
            archive.write_bytes(b"archive")
            self.assertEqual(releaser.create_release("package-1.0.0", "Package"), release.html_url)
            self.assertEqual(releaser.upload_asset("package-1.0.0", archive), uploaded_asset.browser_download_url)
            self.assertTrue(existing_asset.delete_asset.called)
            self.assertEqual(
                releaser.create_release_with_asset("package", "1.0.0", archive),
                (release.html_url, uploaded_asset.browser_download_url),
            )
            self.assertEqual(
                releaser.get_release_asset_url("package", "1.0.0", "package.tgz"),
                uploaded_asset.browser_download_url,
            )
            self.assertTrue(releaser.release_exists("package", "1.0.0"))

    @patch("salt_bundle.storage.providers.github_provider.GitHubReleaser")
    def test_github_provider_uses_client_and_git_root(self, releaser_class: MagicMock) -> None:
        client = releaser_class.return_value
        client.repo.name = "repository"
        provider = GitHubReleaseProvider(token="token", repository="owner/repository")
        provider.initialize()
        with patch("salt_bundle.storage.providers.github_provider.subprocess.run") as run:
            run.return_value = MagicMock(returncode=0, stdout="/tmp/repository\n")
            self.assertEqual(provider._find_git_root(), Path("/tmp/repository"))
        provider._git_root = None
        with patch("salt_bundle.storage.providers.github_provider.subprocess.run", side_effect=FileNotFoundError):
            self.assertIsNone(provider._find_git_root())

        provider._git_root = Path("/tmp/repository")
        with patch.object(provider, "_commit_index_to_branch") as commit:
            provider.save_index(Index(generated="2024-01-01T00:00:00"))
            commit.assert_called_once()
        client.create_release_with_asset.return_value = ("release", "asset")
        self.assertEqual(provider.upload_package("package", "1.0.0", Path("archive.tgz")), "asset")
        client.release_exists.return_value = True
        self.assertTrue(provider.package_exists("package", "1.0.0"))
