"""
Functional tests: CLI end-to-end workflows.

Verifies that salt-bundle CLI commands work correctly with real
package operations (init, pack, verify, project init).
"""

import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

from conftest import requires_salt


def run_salt_bundle(*args: str, cwd: str | Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run salt-bundle CLI command."""
    cmd = ["salt-bundle", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
    )


pytestmark = requires_salt


class TestProjectInit:
    """salt-bundle project init command."""

    def test_project_init_creates_saltfile(self, tmp_path):
        """project init should create a Saltfile."""
        r = run_salt_bundle("project", "init", "--force", cwd=tmp_path)
        assert r.returncode == 0, r.stderr
        saltfile = tmp_path / "Saltfile"
        assert saltfile.exists()
        data = yaml.safe_load(saltfile.read_text())
        assert "vendor_dir" in data

    def test_project_init_idempotent_with_force(self, tmp_path):
        """project init --force should succeed even if Saltfile exists."""
        (tmp_path / "Saltfile").write_text("vendor_dir: vendor\n")
        r = run_salt_bundle("project", "init", "--force", cwd=tmp_path)
        assert r.returncode == 0, r.stderr


class TestPackageInit:
    """salt-bundle package init command."""

    def test_formula_init_creates_metadata(self, tmp_path):
        """package init --type=formula should create FORMULA file."""
        r = run_salt_bundle(
            "package", "init", "--force", "--type=formula",
            cwd=tmp_path,
        )
        assert r.returncode == 0, r.stderr
        assert (tmp_path / "FORMULA").exists()

    def test_extension_init_creates_metadata(self, tmp_path):
        """package init --type=extension should create EXTENSION file."""
        r = run_salt_bundle(
            "package", "init", "--force", "--type=extension",
            cwd=tmp_path,
        )
        assert r.returncode == 0, r.stderr
        assert (tmp_path / "EXTENSION").exists()


class TestPackagePack:
    """salt-bundle package pack command."""

    def test_pack_formula(self, tmp_path):
        """Pack a formula into a .tar.gz archive."""
        # Create a minimal formula
        formula_dir = tmp_path / "my-formula"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text(yaml.dump({
            "name": "my-formula",
            "version": "1.0.0",
            "description": "Test formula",
        }))
        (formula_dir / "init.sls").write_text("# init\n")
        modules_dir = formula_dir / "_modules"
        modules_dir.mkdir()
        (modules_dir / "my_mod.py").write_text(textwrap.dedent("""\
            def ping():
                return "pong"
        """))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        r = run_salt_bundle(
            "package", "pack", "-o", str(output_dir),
            cwd=formula_dir,
        )
        assert r.returncode == 0, r.stderr

        # Should produce a tar.gz archive
        archives = list(output_dir.glob("*.tar.gz"))
        assert len(archives) == 1
        assert "my-formula" in archives[0].name
        assert "1.0.0" in archives[0].name

    def test_pack_creates_valid_archive(self, tmp_path):
        """Packed archive should be extractable and contain expected files."""
        import tarfile

        formula_dir = tmp_path / "test-pkg"
        formula_dir.mkdir()
        (formula_dir / "FORMULA").write_text(yaml.dump({
            "name": "test-pkg",
            "version": "0.1.0",
            "description": "Archive test",
        }))
        (formula_dir / "init.sls").write_text("# init\n")
        states_dir = formula_dir / "_states"
        states_dir.mkdir()
        (states_dir / "my_state.py").write_text("def run(name): pass\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        r = run_salt_bundle("package", "pack", "-o", str(output_dir), cwd=formula_dir)
        assert r.returncode == 0, r.stderr

        archive = list(output_dir.glob("*.tar.gz"))[0]
        with tarfile.open(archive, "r:gz") as tar:
            names = tar.getnames()
            assert any("init.sls" in n for n in names)
            assert any("my_state.py" in n for n in names)


class TestPackageVerify:
    """salt-bundle package verify command."""

    def test_verify_valid_project(self, tmp_path):
        """Verify should pass for a project with matching lock and vendor."""
        # Create Saltfile
        (tmp_path / "Saltfile").write_text(yaml.dump({
            "vendor_dir": "vendor",
            "dependencies": [{"name": "foo", "version": "0.1.1"}],
        }))

        # Create lock file
        (tmp_path / "Saltfile.lock").write_text(yaml.dump({
            "dependencies": {
                "foo": {
                    "version": "0.1.1",
                    "type": "formula",
                    "repository": "local",
                    "url": "file:///foo-0.1.1.tar.gz",
                    "digest": "sha256:0000",
                    "dependencies": {},
                },
            },
        }))

        # Create vendor with matching package
        vendor_foo = tmp_path / "vendor" / "foo"
        vendor_foo.mkdir(parents=True)
        (vendor_foo / "FORMULA").write_text(yaml.dump({
            "name": "foo",
            "version": "0.1.1",
            "description": "Foo",
        }))

        r = run_salt_bundle("package", "verify", cwd=tmp_path)
        assert r.returncode == 0, r.stderr

    def test_verify_missing_package_fails(self, tmp_path):
        """Verify should fail when a locked package is missing from vendor."""
        (tmp_path / "Saltfile").write_text(yaml.dump({
            "vendor_dir": "vendor",
            "dependencies": [{"name": "missing-pkg", "version": "1.0.0"}],
        }))

        (tmp_path / "Saltfile.lock").write_text(yaml.dump({
            "dependencies": {
                "missing-pkg": {
                    "version": "1.0.0",
                    "type": "formula",
                    "repository": "local",
                    "url": "file:///missing.tar.gz",
                    "digest": "sha256:0000",
                    "dependencies": {},
                },
            },
        }))

        (tmp_path / "vendor").mkdir()

        r = run_salt_bundle("package", "verify", cwd=tmp_path)
        assert r.returncode != 0


class TestRepoIndex:
    """salt-bundle repo index command."""

    def test_generate_index_from_archives(self, tmp_path):
        """repo index should generate index.yaml from tar.gz files."""
        import tarfile

        # Create a simple package archive
        formula_dir = tmp_path / "build" / "my-pkg"
        formula_dir.mkdir(parents=True)
        (formula_dir / "FORMULA").write_text(yaml.dump({
            "name": "my-pkg",
            "version": "1.0.0",
            "description": "Index test",
        }))
        (formula_dir / "init.sls").write_text("# init\n")

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        archive_path = repo_dir / "my-pkg-1.0.0.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(formula_dir / "FORMULA", arcname="FORMULA")
            tar.add(formula_dir / "init.sls", arcname="init.sls")

        r = run_salt_bundle(
            "repo", "index", str(repo_dir),
            "-u", "https://example.com/repo/",
            cwd=tmp_path,
        )
        assert r.returncode == 0, r.stderr

        index_file = repo_dir / "index.yaml"
        assert index_file.exists()
        index_data = yaml.safe_load(index_file.read_text())
        assert "packages" in index_data
        assert "my-pkg" in index_data["packages"]
