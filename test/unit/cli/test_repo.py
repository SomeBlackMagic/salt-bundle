import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from salt_bundle.cli.repo.index import index
from salt_bundle.cli.repo.release import release


class TestRepoIndexCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temporary_directory.name)
        self.context = {"PROJECT_DIR": self.repo_dir, "DEBUG": True, "QUIET": True}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_index_generates_from_tgz_files(self) -> None:
        # Create a formula and pack it
        from salt_bundle.packaging.archives import pack_formula

        formula_dir = self.repo_dir / "source"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        pack_formula(formula_dir, self.repo_dir)

        result = self.runner.invoke(index, [str(self.repo_dir)], obj=self.context)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Generated index with 1 packages", result.output)
        self.assertTrue((self.repo_dir / "index.yaml").exists())

    def test_index_with_output_dir(self) -> None:
        from salt_bundle.packaging.archives import pack_formula

        formula_dir = self.repo_dir / "source"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        pack_formula(formula_dir, self.repo_dir)

        output_dir = self.repo_dir / "output"
        result = self.runner.invoke(
            index, [str(self.repo_dir), "--output-dir", str(output_dir)], obj=self.context
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Index saved to:", result.output)
        self.assertTrue((output_dir / "index.yaml").exists())

    def test_index_fails_on_empty_directory(self) -> None:
        empty_dir = self.repo_dir / "empty"
        empty_dir.mkdir()
        result = self.runner.invoke(index, [str(empty_dir)], obj=self.context)
        self.assertNotEqual(result.exit_code, 0)


class TestRepoReleaseCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.context = {"PROJECT_DIR": self.root, "DEBUG": True, "QUIET": True}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_release_local_provider_success(self) -> None:
        formulas_dir = self.root / "formulas" / "example"
        formulas_dir.mkdir(parents=True)
        (formulas_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (formulas_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        storage_dir = self.root / "repo"
        result = self.runner.invoke(release, [
            "--formulas-dir", str(self.root / "formulas"),
            "--provider", "local",
            "--pkg-storage-dir", str(storage_dir),
        ], obj=self.context)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Released 1 package(s)", result.output)

    def test_release_local_provider_dry_run(self) -> None:
        formulas_dir = self.root / "formulas" / "example"
        formulas_dir.mkdir(parents=True)
        (formulas_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
        (formulas_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        storage_dir = self.root / "repo"
        result = self.runner.invoke(release, [
            "--formulas-dir", str(self.root / "formulas"),
            "--provider", "local",
            "--pkg-storage-dir", str(storage_dir),
            "--dry-run",
        ], obj=self.context)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("DRY RUN", result.output)
        self.assertFalse(storage_dir.exists())

    def test_release_local_provider_missing_pkg_storage_dir(self) -> None:
        formulas_dir = self.root / "formulas"
        formulas_dir.mkdir()
        result = self.runner.invoke(release, [
            "--formulas-dir", str(formulas_dir),
            "--provider", "local",
        ], obj=self.context)
        self.assertNotEqual(result.exit_code, 0)

    def test_release_single_formula(self) -> None:
        formula_dir = self.root / "my-formula"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text("name: my-formula\nversion: 1.0.0\n", encoding="utf-8")
        (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

        storage_dir = self.root / "repo"
        result = self.runner.invoke(release, [
            "--formulas-dir", str(formula_dir),
            "--single",
            "--provider", "local",
            "--pkg-storage-dir", str(storage_dir),
        ], obj=self.context)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Released 1 package(s)", result.output)

    def test_release_github_provider_missing_env(self) -> None:
        formulas_dir = self.root / "formulas"
        formulas_dir.mkdir()
        with patch.dict("os.environ", {}, clear=True):
            result = self.runner.invoke(release, [
                "--formulas-dir", str(formulas_dir),
                "--provider", "github",
            ], obj=self.context)
        self.assertNotEqual(result.exit_code, 0)

    def test_release_no_valid_formulas(self) -> None:
        formulas_dir = self.root / "formulas"
        formulas_dir.mkdir()

        storage_dir = self.root / "repo"
        result = self.runner.invoke(release, [
            "--formulas-dir", str(formulas_dir),
            "--provider", "local",
            "--pkg-storage-dir", str(storage_dir),
        ], obj=self.context)

        self.assertNotEqual(result.exit_code, 0)
