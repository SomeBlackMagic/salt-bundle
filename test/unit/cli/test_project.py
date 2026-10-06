import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from types import SimpleNamespace


from salt_bundle.cli.project.update import update
from salt_bundle.cli.project.install import install
from salt_bundle.dependencies.index_models import Index, IndexEntry
from salt_bundle.packaging.models import FormulaDependency
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

    @patch('salt_bundle.cli.project.update.fetch_index')
    @patch('salt_bundle.cli.project.update.download_package')
    @patch('salt_bundle.storage.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_update_success_with_transitive(self, mock_run, mock_install_vendor, mock_download, mock_fetch_index):
        """Positive scenario: successful resolution and installation with transitive dependencies."""
        # Project setup
        deps_yaml = self.project_dir / "Saltfile"
        deps_yaml.write_text("""
dependencies:
  - name: acme/foo
    version: "^1.0.0"
    source: http://repo.example.com
""")

        # Repository index setup
        # foo depends on bar
        foo_entry = IndexEntry(
            version="1.0.0",
            url="foo-1.0.0.tgz",
            digest="sha256:foo_hash",
            dependencies=[FormulaDependency(name="acme/bar", version=">=0.5.0")]
        )
        bar_entry = IndexEntry(
            version="0.6.0",
            url="bar-0.6.0.tgz",
            digest="sha256:bar_hash"
        )

        mock_index = Index(generated="2023-01-01T00:00:00", packages={
            "acme/foo": [foo_entry],
            "acme/bar": [bar_entry]
        })
        mock_fetch_index.return_value = mock_index
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        # Run update command
        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 0)
        self.assertIn("✓ acme/foo 1.0.0 from http://repo.example.com", result.output)
        self.assertIn("✓ acme/bar 0.6.0 from http://repo.example.com", result.output)

        # Check lock file creation
        lock_file = self.project_dir / "Saltfile.lock"
        self.assertTrue(lock_file.exists())

        # Check download and install calls
        self.assertEqual(mock_download.call_count, 2)
        self.assertEqual(mock_install_vendor.call_count, 2)

    @patch('salt_bundle.cli.project.update.fetch_index')
    def test_update_fail_unresolved_dependency(self, mock_fetch_index):
        """Negative scenario: unable to resolve dependency."""
        deps_yaml = self.project_dir / "Saltfile"
        deps_yaml.write_text("""
dependencies:
  - name: acme/nonexistent
    version: "1.0.0"
    source: http://repo.example.com
""")

        mock_index = Index(generated="2023-01-01T00:00:00", packages={})
        mock_fetch_index.return_value = mock_index

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: Could not resolve dependency: acme/nonexistent 1.0.0", result.output)

    @patch('salt_bundle.cli.project.update.fetch_index')
    def test_update_rejects_extension_dependency_on_formula(self, mock_fetch_index):
        (self.project_dir / "Saltfile").write_text(
            """dependencies:
  - name: acme/extension
    version: "1.0.0"
    source: http://repo.example.com
""",
            encoding="utf-8",
        )
        mock_fetch_index.return_value = Index(
            generated="2023-01-01T00:00:00",
            packages={
                "acme/extension": [
                    IndexEntry(
                        version="1.0.0",
                        url="extension-1.0.0.tgz",
                        digest="sha256:extension_hash",
                        type="extension",
                        dependencies=[FormulaDependency(name="acme/formula", version="1.0.0")],
                    )
                ],
                "acme/formula": [
                    IndexEntry(
                        version="1.0.0",
                        url="formula-1.0.0.tgz",
                        digest="sha256:formula_hash",
                        type="formula",
                    )
                ],
            },
        )

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 1)
        self.assertIn("cannot resolve to a formula", result.output)

    @patch('salt_bundle.cli.project.update.fetch_index')
    @patch('salt_bundle.cli.project.update.download_package')
    def test_update_fail_digest_mismatch(self, mock_download, mock_fetch_index):
        """Negative scenario: error on digest mismatch."""
        deps_yaml = self.project_dir / "Saltfile"
        deps_yaml.write_text("""
dependencies:
  - name: acme/foo
    version: "1.0.0"
    source: http://repo.example.com
""")

        foo_entry = IndexEntry(
            version="1.0.0",
            url="foo-1.0.0.tgz",
            digest="sha256:correct_hash"
        )
        mock_fetch_index.return_value = Index(generated="2023-01-01T00:00:00", packages={"acme/foo": [foo_entry]})

        # Simulate error in download_package
        mock_download.side_effect = ValueError("Digest mismatch for foo-1.0.0.tgz")

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: Digest mismatch for foo-1.0.0.tgz", result.output)

    @patch('salt_bundle.cli.project.install.download_package')
    @patch('salt_bundle.storage.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_install_success_from_lock(self, mock_run, mock_install_vendor, mock_download):
        """Positive scenario: installation from existing lock file."""
        # Project setup
        deps_yaml = self.project_dir / "Saltfile"
        deps_yaml.write_text("""
dependencies:
  - name: acme/foo
    version: "1.0.0"
    source: http://repo.example.com
""")

        lock_file = self.project_dir / "Saltfile.lock"
        lock_file.write_text("""
dependencies:
  acme/foo:
    version: 1.0.0
    repository: http://repo.example.com
    url: foo-1.0.0.tgz
    digest: sha256:foo_hash
""")

        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(install, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Installing acme/foo 1.0.0...", result.output)
        mock_download.assert_called_with("foo-1.0.0.tgz", "http://repo.example.com", "sha256:foo_hash")
        self.assertEqual(mock_install_vendor.call_count, 1)

    def test_install_fail_no_lock(self):
        """Negative scenario: running install without lock file."""
        deps_yaml = self.project_dir / "Saltfile"
        deps_yaml.write_text("dependencies: []")

        result = self.runner.invoke(install, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: Saltfile.lock not found.", result.output)

    def test_update_installs_snapshot_from_relative_path_source(self):
        source_dir = Path(self.test_dir) / "formulas" / "nginx"
        source_dir.mkdir(parents=True)
        (source_dir / "FORMULA").write_text(
            "name: nginx\nversion: 1.2.0\n", encoding="utf-8"
        )
        (source_dir / "init.sls").write_text("nginx: []\n", encoding="utf-8")
        (self.project_dir / "Saltfile").write_text(
            """dependencies:
  - name: legacy/nginx
    source: path://../formulas/nginx
""",
            encoding="utf-8",
        )

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 0, result.output)
        installed_dir = self.project_dir / "vendor" / "legacy" / "nginx"
        self.assertEqual((installed_dir / "init.sls").read_text(encoding="utf-8"), "nginx: []\n")
        locked = (self.project_dir / "Saltfile.lock").read_text(encoding="utf-8")
        self.assertIn("source_type: path", locked)
        self.assertIn("linked: false", locked)

    def test_update_links_path_source_when_dependency_requests_link_mode(self):
        source_dir = Path(self.test_dir) / "formulas" / "nginx"
        source_dir.mkdir(parents=True)
        (source_dir / "FORMULA").write_text(
            "name: nginx\nversion: 1.2.0\n", encoding="utf-8"
        )
        (source_dir / "init.sls").write_text("nginx: []\n", encoding="utf-8")
        (self.project_dir / "Saltfile").write_text(
            """dependencies:
  - name: legacy/nginx
    source: path://../formulas/nginx
    link: true
""",
            encoding="utf-8",
        )

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 0, result.output)
        installed_dir = self.project_dir / "vendor" / "legacy" / "nginx"
        self.assertTrue(installed_dir.is_symlink())
        self.assertEqual(installed_dir.resolve(), source_dir.resolve())
        locked = (self.project_dir / "Saltfile.lock").read_text(encoding="utf-8")
        self.assertIn("digest: linked", locked)
        self.assertIn("linked: true", locked)

    def test_update_reports_a_missing_path_source(self):
        missing_dir = Path(self.test_dir) / "formulas" / "missing"
        (self.project_dir / "Saltfile").write_text(
            """dependencies:
  - name: legacy/missing
    source: path://../formulas/missing
""",
            encoding="utf-8",
        )

        result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 1)
        self.assertIn(f"Error: source path not found: {missing_dir}", result.output)

    @patch('salt_bundle.cli.project.update.fetch_index')
    @patch('salt_bundle.cli.project.update.download_package')
    @patch('salt_bundle.storage.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_update_uses_saltfile_repositories_for_resolution(
        self, mock_run, mock_install_vendor, mock_download, mock_fetch_index
    ):
        """Repositories defined in Saltfile should be used for dependency resolution."""
        (self.project_dir / "Saltfile").write_text(
            """repositories:
  - name: company
    url: https://company.example.test/salt/
dependencies:
  - name: acme/nginx
    version: "^1.0.0"
""",
            encoding="utf-8",
        )

        nginx_entry = IndexEntry(
            version="1.2.0",
            url="nginx-1.2.0.tgz",
            digest="sha256:nginx_hash",
        )
        mock_fetch_index.return_value = Index(
            generated="2023-01-01T00:00:00",
            packages={"acme/nginx": [nginx_entry]},
        )
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(update, obj={"PROJECT_DIR": self.project_dir, "DEBUG": True})

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("✓ acme/nginx 1.2.0 from https://company.example.test/salt/", result.output)
        mock_fetch_index.assert_called_with("https://company.example.test/salt/")

    @patch('salt_bundle.cli.project.update.fetch_index')
    @patch('salt_bundle.cli.project.update.download_package')
    @patch('salt_bundle.storage.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_update_saltfile_repositories_take_priority_over_global(
        self, mock_run, mock_install_vendor, mock_download, mock_fetch_index
    ):
        """Saltfile repositories should be checked before global user repositories."""
        (self.project_dir / "Saltfile").write_text(
            """repositories:
  - name: local-repo
    url: https://local.example.test/salt/
dependencies:
  - name: acme/nginx
    version: "1.0.0"
""",
            encoding="utf-8",
        )

        local_index = Index(
            generated="2023-01-01T00:00:00",
            packages={
                "acme/nginx": [
                    IndexEntry(
                        version="1.0.0",
                        url="nginx-1.0.0.tgz",
                        digest="sha256:local_hash",
                    )
                ],
            },
        )
        global_index = Index(
            generated="2023-01-01T00:00:00",
            packages={
                "acme/nginx": [
                    IndexEntry(
                        version="1.0.0",
                        url="nginx-1.0.0.tgz",
                        digest="sha256:global_hash",
                    )
                ],
            },
        )

        def fake_fetch_index(source):
            if source == "https://local.example.test/salt/":
                return local_index
            return global_index

        mock_fetch_index.side_effect = fake_fetch_index
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        with patch(
            "salt_bundle.cli.project.update.load_user_config",
            return_value=SimpleNamespace(
                repositories=[
                    SimpleNamespace(url="https://global.example.test/salt/", type="remote")
                ]
            ),
        ):
            result = self.runner.invoke(update, obj={"PROJECT_DIR": self.project_dir, "DEBUG": True})

        self.assertEqual(result.exit_code, 0, result.output)
        # Package resolved from local repo, not global
        self.assertIn("✓ acme/nginx 1.0.0 from https://local.example.test/salt/", result.output)
        # Global repo should not have been queried
        mock_fetch_index.assert_called_once_with("https://local.example.test/salt/")

    @patch('salt_bundle.cli.project.update.fetch_index')
    @patch('salt_bundle.cli.project.update.download_package')
    @patch('salt_bundle.storage.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_update_falls_back_to_global_repos_when_saltfile_repos_miss(
        self, mock_run, mock_install_vendor, mock_download, mock_fetch_index
    ):
        """If Saltfile repos don't have the package, global repos should be checked."""
        (self.project_dir / "Saltfile").write_text(
            """repositories:
  - name: local-repo
    url: https://local.example.test/salt/
dependencies:
  - name: acme/nginx
    version: "1.0.0"
""",
            encoding="utf-8",
        )

        local_index = Index(
            generated="2023-01-01T00:00:00",
            packages={},
        )
        global_index = Index(
            generated="2023-01-01T00:00:00",
            packages={
                "acme/nginx": [
                    IndexEntry(
                        version="1.0.0",
                        url="nginx-1.0.0.tgz",
                        digest="sha256:global_hash",
                    )
                ],
            },
        )

        def fake_fetch_index(source):
            if source == "https://local.example.test/salt/":
                return local_index
            return global_index

        mock_fetch_index.side_effect = fake_fetch_index
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        with patch(
            "salt_bundle.cli.project.update.load_user_config",
            return_value=SimpleNamespace(
                repositories=[
                    SimpleNamespace(url="https://global.example.test/salt/", type="remote")
                ]
            ),
        ):
            result = self.runner.invoke(update, obj={"PROJECT_DIR": self.project_dir, "DEBUG": True})

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("✓ acme/nginx 1.0.0 from https://global.example.test/salt/", result.output)

    @patch('salt_bundle.cli.project.update.fetch_index')
    @patch('salt_bundle.cli.project.update.download_package')
    @patch('salt_bundle.storage.vendor.install_package_to_vendor')
    @patch('subprocess.run')
    def test_update_explicit_source_overrides_all_repositories(
        self, mock_run, mock_install_vendor, mock_download, mock_fetch_index
    ):
        """Explicit dependency source should override both Saltfile and global repos."""
        (self.project_dir / "Saltfile").write_text(
            """repositories:
  - name: local-repo
    url: https://local.example.test/salt/
dependencies:
  - name: acme/nginx
    version: "1.0.0"
    source: https://explicit.example.test/salt/
""",
            encoding="utf-8",
        )

        explicit_index = Index(
            generated="2023-01-01T00:00:00",
            packages={
                "acme/nginx": [
                    IndexEntry(
                        version="1.0.0",
                        url="nginx-1.0.0.tgz",
                        digest="sha256:explicit_hash",
                    )
                ],
            },
        )
        mock_fetch_index.return_value = explicit_index
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(update, obj={"PROJECT_DIR": self.project_dir, "DEBUG": True})

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("✓ acme/nginx 1.0.0 from https://explicit.example.test/salt/", result.output)
        mock_fetch_index.assert_called_once_with("https://explicit.example.test/salt/")

    def test_update_resolves_dependency_from_global_path_source_repository(self):
        repository_dir = Path(self.test_dir) / "formulas"
        source_dir = repository_dir / "nginx"
        source_dir.mkdir(parents=True)
        (source_dir / "FORMULA").write_text(
            "name: nginx\nversion: 1.2.0\n", encoding="utf-8"
        )
        (source_dir / "init.sls").write_text("nginx: []\n", encoding="utf-8")
        (self.project_dir / "Saltfile").write_text(
            "dependencies:\n  - name: legacy/nginx\n", encoding="utf-8"
        )

        with patch(
            "salt_bundle.cli.project.update.load_user_config",
            return_value=SimpleNamespace(
                repositories=[
                    SimpleNamespace(url=str(repository_dir), type="path-source")
                ]
            ),
        ):
            result = self.runner.invoke(update, obj={'PROJECT_DIR': self.project_dir, 'DEBUG': True})

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue((self.project_dir / "vendor" / "legacy" / "nginx" / "init.sls").is_file())

if __name__ == '__main__':
    unittest.main()
