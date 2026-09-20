import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from salt_bundle.cli.package.verify import verify


class TestVerifyExtended(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.context = {"PROJECT_DIR": self.project_dir, "DEBUG": True, "QUIET": True}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_verify_empty_lock_file_succeeds(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        # No Saltfile.lock - load_lockfile returns empty LockFile
        result = self.runner.invoke(verify, obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("All dependencies verified", result.output)

    def test_verify_missing_package_reports_error(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        (self.project_dir / "Saltfile.lock").write_text(
            "dependencies:\n  missing:\n    version: 1.0.0\n    repository: source\n    url: missing.tgz\n    digest: sha256:abc\n",
            encoding="utf-8",
        )
        vendor_dir = self.project_dir / "vendor"
        vendor_dir.mkdir()

        result = self.runner.invoke(verify, obj=self.context)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Errors found", result.output)

    def test_verify_missing_metadata_reports_error(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        (self.project_dir / "Saltfile.lock").write_text(
            "dependencies:\n  example:\n    version: 1.0.0\n    repository: source\n    url: example.tgz\n    digest: sha256:abc\n",
            encoding="utf-8",
        )
        pkg_dir = self.project_dir / "vendor" / "example"
        pkg_dir.mkdir(parents=True)
        # No FORMULA or EXTENSION file

        result = self.runner.invoke(verify, obj=self.context)
        self.assertNotEqual(result.exit_code, 0)

    def test_verify_extension_package(self) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        (self.project_dir / "Saltfile.lock").write_text(
            "dependencies:\n  example:\n    version: 1.0.0\n    repository: source\n    url: example.tgz\n    digest: sha256:abc\n",
            encoding="utf-8",
        )
        pkg_dir = self.project_dir / "vendor" / "example"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "EXTENSION").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")

        result = self.runner.invoke(verify, obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("All dependencies verified", result.output)
