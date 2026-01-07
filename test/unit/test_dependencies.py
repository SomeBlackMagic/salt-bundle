import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil


from salt_bundle.cli.project.update import update
from salt_bundle.cli.project.install import install
from salt_bundle.models.index_models import Index, IndexEntry
from salt_bundle.models.package_models import PackageDependency
from click.testing import CliRunner

class TestProjectCommands(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "project"
        self.project_dir.mkdir()
        
        # Mock user config to avoid dependency on real environment
        self.user_config_patcher = patch('salt_bundle.config.load_user_config')
        self.mock_user_config = self.user_config_patcher.start()
        self.mock_user_config.return_value.repositories = []

    def tearDown(self):
        self.user_config_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch('salt_bundle.repository.fetch_index')
    @patch('salt_bundle.repository.download_package')
    @patch('salt_bundle.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_update_success_with_transitive(self, mock_run, mock_install_vendor, mock_download, mock_fetch_index):
        """Positive scenario: successful resolution and installation with transitive dependencies."""
        # Project setup
        deps_yaml = self.project_dir / ".salt-dependencies.yaml"
        deps_yaml.write_text("""
project: test-project
repositories:
  - name: main
    url: http://repo.example.com
dependencies:
  foo: "^1.0.0"
""")

        # Repository index setup
        # foo depends on bar
        foo_entry = IndexEntry(
            version="1.0.0",
            url="foo-1.0.0.tgz",
            digest="sha256:foo_hash",
            dependencies=[PackageDependency(name="bar", version=">=0.5.0")]
        )
        bar_entry = IndexEntry(
            version="0.6.0",
            url="bar-0.6.0.tgz",
            digest="sha256:bar_hash"
        )
        
        mock_index = Index(generated="2023-01-01T00:00:00", packages={
            "foo": [foo_entry],
            "bar": [bar_entry]
        })
        mock_fetch_index.return_value = mock_index
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        # Run update command
        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("✓ foo 1.0.0 from main", result.output)
        self.assertIn("✓ bar 0.6.0 from main", result.output)
        
        # Check lock file creation
        lock_file = self.project_dir / ".salt-dependencies.lock"
        self.assertTrue(lock_file.exists())
        
        # Check download and install calls
        self.assertEqual(mock_download.call_count, 2)
        self.assertEqual(mock_install_vendor.call_count, 2)

    @patch('salt_bundle.repository.fetch_index')
    def test_update_fail_unresolved_dependency(self, mock_fetch_index):
        """Negative scenario: unable to resolve dependency."""
        deps_yaml = self.project_dir / ".salt-dependencies.yaml"
        deps_yaml.write_text("""
project: test-project
repositories:
  - name: main
    url: http://repo.example.com
dependencies:
  nonexistent: "1.0.0"
""")
        
        mock_index = Index(generated="2023-01-01T00:00:00", packages={})
        mock_fetch_index.return_value = mock_index

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: Could not resolve dependency: nonexistent 1.0.0", result.output)

    @patch('salt_bundle.repository.fetch_index')
    @patch('salt_bundle.repository.download_package')
    def test_update_fail_digest_mismatch(self, mock_download, mock_fetch_index):
        """Negative scenario: error on digest mismatch."""
        deps_yaml = self.project_dir / ".salt-dependencies.yaml"
        deps_yaml.write_text("""
project: test-project
repositories:
  - name: main
    url: http://repo.example.com
dependencies:
  foo: "1.0.0"
""")
        
        foo_entry = IndexEntry(
            version="1.0.0",
            url="foo-1.0.0.tgz",
            digest="sha256:correct_hash"
        )
        mock_fetch_index.return_value = Index(generated="2023-01-01T00:00:00", packages={"foo": [foo_entry]})
        
        # Simulate error in download_package
        mock_download.side_effect = ValueError("Digest mismatch for foo-1.0.0.tgz")

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: Digest mismatch for foo-1.0.0.tgz", result.output)

    @patch('salt_bundle.repository.download_package')
    @patch('salt_bundle.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_install_success_from_lock(self, mock_run, mock_install_vendor, mock_download):
        """Positive scenario: installation from existing lock file."""
        # Project setup
        deps_yaml = self.project_dir / ".salt-dependencies.yaml"
        deps_yaml.write_text("""
project: test-project
repositories:
  - name: main
    url: http://repo.example.com
dependencies:
  foo: "1.0.0"
""")
        
        lock_file = self.project_dir / ".salt-dependencies.lock"
        lock_file.write_text("""
dependencies:
  foo:
    version: 1.0.0
    repository: main
    url: foo-1.0.0.tgz
    digest: sha256:foo_hash
""")
        
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(install, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Installing foo 1.0.0...", result.output)
        mock_download.assert_called_with("foo-1.0.0.tgz", "http://repo.example.com", "sha256:foo_hash")
        self.assertEqual(mock_install_vendor.call_count, 1)

    def test_install_fail_no_lock(self):
        """Negative scenario: running install without lock file."""
        deps_yaml = self.project_dir / ".salt-dependencies.yaml"
        deps_yaml.write_text("project: test-project")
        
        result = self.runner.invoke(install, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: .salt-dependencies.lock not found.", result.output)

if __name__ == '__main__':
    unittest.main()
