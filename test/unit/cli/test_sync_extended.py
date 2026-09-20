import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from salt_bundle.cli.package.sync import sync


class TestSyncExtended(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.context = {"PROJECT_DIR": self.project_dir, "DEBUG": True, "QUIET": False}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_sync_no_modules_found(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        vendor_dir = self.project_dir / "vendor" / "example"
        vendor_dir.mkdir(parents=True)
        (vendor_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        cache_dir = self.project_dir / "cache"

        with patch("salt_bundle.cli.package.sync.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.runner.invoke(sync, ["--cache-dir", str(cache_dir)], obj=self.context)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("No modules found to sync", result.output)

    @patch("salt_bundle.cli.package.sync.subprocess.run")
    def test_sync_multiple_module_types(self, mock_run) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        vendor_dir = self.project_dir / "vendor" / "example"
        for mod_type in ("_modules", "_states", "_grains"):
            mod_dir = vendor_dir / mod_type
            mod_dir.mkdir(parents=True)
            (mod_dir / "example.py").write_text("", encoding="utf-8")
        cache_dir = self.project_dir / "cache"
        mock_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(sync, ["--cache-dir", str(cache_dir)], obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Synced 3 module(s)", result.output)
        self.assertTrue((cache_dir / "modules" / "example.py").exists())
        self.assertTrue((cache_dir / "states" / "example.py").exists())
        self.assertTrue((cache_dir / "grains" / "example.py").exists())

    @patch("salt_bundle.cli.package.sync.subprocess.run", side_effect=FileNotFoundError)
    def test_sync_salt_call_not_found(self, mock_run) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        vendor_dir = self.project_dir / "vendor" / "example"
        mod_dir = vendor_dir / "_modules"
        mod_dir.mkdir(parents=True)
        (mod_dir / "example.py").write_text("", encoding="utf-8")
        cache_dir = self.project_dir / "cache"

        result = self.runner.invoke(sync, ["--cache-dir", str(cache_dir)], obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("salt-call not found", result.output)

    @patch("salt_bundle.cli.package.sync.subprocess.run")
    def test_sync_salt_call_failure(self, mock_run) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        vendor_dir = self.project_dir / "vendor" / "example"
        mod_dir = vendor_dir / "_modules"
        mod_dir.mkdir(parents=True)
        (mod_dir / "example.py").write_text("", encoding="utf-8")
        cache_dir = self.project_dir / "cache"
        mock_run.return_value = MagicMock(returncode=1, stderr="salt error")

        result = self.runner.invoke(sync, ["--cache-dir", str(cache_dir)], obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Failed to sync Salt extensions", result.output)

    def test_sync_auto_detect_no_config_fails(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        (self.project_dir / "vendor").mkdir()

        with patch("salt_bundle.salt.loader._find_project_config", return_value=None):
            result = self.runner.invoke(sync, obj=self.context)

        # Should fail because can't auto-detect cache dir
        self.assertIn("Error", result.output)

    def test_sync_skips_hidden_dirs(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        vendor_dir = self.project_dir / "vendor"
        hidden_dir = vendor_dir / ".hidden" / "_modules"
        hidden_dir.mkdir(parents=True)
        (hidden_dir / "example.py").write_text("", encoding="utf-8")
        cache_dir = self.project_dir / "cache"

        with patch("salt_bundle.cli.package.sync.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.runner.invoke(sync, ["--cache-dir", str(cache_dir)], obj=self.context)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("No modules found to sync", result.output)
