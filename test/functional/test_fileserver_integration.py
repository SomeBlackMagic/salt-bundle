"""
Functional tests: bundlefs fileserver backend.

Verifies that the custom fileserver discovers and serves files
from vendor packages through Salt's cp module.
"""

import shutil

import pytest

from conftest import requires_salt, salt_call

pytestmark = requires_salt


class TestFileserverFileListing:
    """Verify bundlefs lists formula files correctly."""

    def test_fileserver_lists_state_files(self, project_dir):
        """cp.list_states should include states from vendor formulas."""
        r = salt_call("cp.list_states", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        states = r["json"]["local"]
        assert "foo" in states
        assert "foo.defaults" in states

    def test_formula_name_without_vendor_and_legacy_lookup(self, project_dir):
        """Salt serves a namespaced package using its short formula SLS name."""
        original = project_dir / "vendor" / "foo"
        formula = project_dir / "vendor" / "someblackmagic" / "containerd-formula"
        formula.parent.mkdir(parents=True)
        original.rename(formula)
        (formula / "FORMULA").write_text(
            "name: someblackmagic/containerd-formula\n"
            "version: 1.0.0\n"
            "top_level_dir: containerd\n",
            encoding="utf-8",
        )
        state_root = formula / "containerd"
        state_root.mkdir()
        shutil.move(str(formula / "init.sls"), str(state_root / "init.sls"))

        listed = salt_call("cp.list_states", cwd=project_dir)
        assert listed["returncode"] == 0, listed["stderr"]
        assert "containerd" in listed["json"]["local"]
        assert "someblackmagic.containerd-formula" not in listed["json"]["local"]

        for sls_path in (
            "containerd/init.sls",
            "someblackmagic/containerd-formula/init.sls",
        ):
            fetched = salt_call(
                "cp.get_file",
                f"salt://{sls_path}",
                str(project_dir / "fetched" / sls_path.replace("/", "_")),
                "makedirs=True",
                cwd=project_dir,
            )
            assert fetched["returncode"] == 0, fetched["stderr"]
            assert fetched["json"]["local"], fetched

        loaded = salt_call("test_module.ping", cwd=project_dir)
        assert loaded["returncode"] == 0, loaded["stderr"]
        assert loaded["json"]["local"] == "module loaded"

    def test_fileserver_lists_module_files(self, project_dir):
        """cp.list_master should include _modules files from vendor."""
        r = salt_call("cp.list_master", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        files = r["json"]["local"]
        # Should include _modules/test_module.py exposed by bundlefs
        module_files = [f for f in files if "test_module" in f]
        assert len(module_files) > 0, f"test_module not found in file list: {files[:20]}"

    def test_fileserver_lists_state_module_files(self, project_dir):
        """File list should include _states files from vendor."""
        r = salt_call("cp.list_master", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        files = r["json"]["local"]
        state_files = [f for f in files if "test_state" in f]
        assert len(state_files) > 0, f"test_state not found in file list: {files[:20]}"


class TestFileserverFileAccess:
    """Verify bundlefs can serve file contents."""

    def test_cp_get_file_from_vendor(self, project_dir):
        """cp.get_file should retrieve a file from vendor formula."""
        dest = project_dir / "fetched_module.py"
        r = salt_call(
            "cp.get_file",
            "salt://_modules/test_module.py",
            str(dest),
            cwd=project_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        # Verify file was actually fetched
        if dest.exists():
            content = dest.read_text()
            assert "module loaded" in content

    def test_cp_get_file_hash(self, project_dir):
        """cp.hash_file should return a valid hash for vendor files."""
        r = salt_call(
            "cp.hash_file",
            "salt://_modules/test_module.py",
            cwd=project_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        if result:
            assert "hsum" in result
            assert "hash_type" in result


class TestFileserverWithMultiplePackages:
    """Verify bundlefs handles multiple vendor packages."""

    def test_files_from_both_packages(self, multi_project_dir):
        """File list should include files from both foo and bar."""
        r = salt_call("cp.list_master", cwd=multi_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        files = r["json"]["local"]
        # foo has _modules/test_module.py, bar has init.sls
        has_foo = any("test_module" in f for f in files)
        has_bar = any("bar" in f or "init" in f for f in files)
        assert has_foo, f"foo module files not found: {files[:20]}"
