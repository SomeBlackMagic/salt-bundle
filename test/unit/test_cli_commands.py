import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from salt_bundle.cli.package.init import init as package_init
from salt_bundle.cli.package.verify import verify
from salt_bundle.cli.package.pack import pack
from salt_bundle.cli.package.sync import sync
from salt_bundle.cli.project.init import init as project_init
from salt_bundle.cli.repo.add import add


class TestCliCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.context = {"PROJECT_DIR": self.project_dir, "DEBUG": True, "QUIET": True}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_initialization_commands_create_manifest_files(self) -> None:
        project_result = self.runner.invoke(project_init, obj=self.context)
        self.assertEqual(project_result.exit_code, 0)
        self.assertTrue((self.project_dir / "Saltfile").exists())
        package_result = self.runner.invoke(
            package_init,
            ["--type", "extension"],
            input="example\n1.0.0\nDescription\n\n\n",
            obj=self.context,
        )
        self.assertEqual(package_result.exit_code, 0)
        self.assertTrue((self.project_dir / "EXTENSION").exists())

    @patch("salt_bundle.cli.repo.add.config.add_user_repository")
    def test_add_repository_reports_success(self, add_repository) -> None:
        result = self.runner.invoke(add, ["--name", "main", "--url", "https://example.test"], obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Added repository globally", result.output)
        add_repository.assert_called_once()

    @patch("salt_bundle.cli.package.sync.subprocess.run")
    def test_sync_copies_extension_modules(self, run) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        module_dir = self.project_dir / "vendor" / "example" / "_modules"
        module_dir.mkdir(parents=True)
        (module_dir / "example.py").write_text("", encoding="utf-8")
        cache_dir = self.project_dir / "cache"
        run.return_value.returncode = 0
        result = self.runner.invoke(sync, ["--cache-dir", str(cache_dir)], obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue((cache_dir / "modules" / "example.py").exists())

    def test_verify_reports_installed_package(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        (self.project_dir / "Saltfile.lock").write_text(
            "dependencies:\n  example:\n    version: 1.0.0\n    repository: source\n    url: example.tgz\n    digest: sha256:abc\n",
            encoding="utf-8",
        )
        package_dir = self.project_dir / "vendor" / "example"
        package_dir.mkdir(parents=True)
        (package_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        result = self.runner.invoke(verify, obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("All dependencies verified", result.output)
