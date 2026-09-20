import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from salt_bundle.cli.package.pack import pack
from salt_bundle.cli.project.vendor import vendor


class TestPackCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.context = {"PROJECT_DIR": self.project_dir, "DEBUG": True, "QUIET": True}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_pack_formula_creates_archive(self) -> None:
        (self.project_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (self.project_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        result = self.runner.invoke(pack, obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Created package:", result.output)

    def test_pack_with_output_dir(self) -> None:
        (self.project_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (self.project_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        output_dir = self.project_dir / "dist"
        output_dir.mkdir()

        result = self.runner.invoke(pack, ["--output-dir", str(output_dir)], obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(any(output_dir.glob("*.tgz")))

    def test_pack_fails_without_metadata(self) -> None:
        result = self.runner.invoke(pack, obj=self.context)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error:", result.output)


class TestVendorCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.context = {"PROJECT_DIR": self.project_dir, "DEBUG": True, "QUIET": True}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_vendor_fails_without_lock(self) -> None:
        (self.project_dir / "Saltfile").write_text("dependencies: []\n", encoding="utf-8")
        result = self.runner.invoke(vendor, obj=self.context)
        self.assertNotEqual(result.exit_code, 0)

    @patch("salt_bundle.cli.project.install.download_package")
    @patch("salt_bundle.storage.vendor.install_package_to_vendor")
    @patch("subprocess.run")
    def test_vendor_installs_from_lock(self, mock_run, mock_install, mock_download) -> None:
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        (self.project_dir / "Saltfile.lock").write_text(
            "dependencies:\n  example:\n    version: 1.0.0\n    repository: source\n    url: example.tgz\n    digest: sha256:abc\n",
            encoding="utf-8",
        )
        mock_download.return_value = Path("/tmp/fake.tgz")
        mock_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(vendor, obj=self.context)
        self.assertEqual(result.exit_code, 0)
