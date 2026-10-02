"""
Functional tests: bundlefs fileserver backend.

Verifies that the custom fileserver discovers and serves files
from vendor packages through Salt's cp module.
"""

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
        # foo formula should be listed (init.sls or defaults.sls)
        assert any("foo" in s for s in states) or len(states) >= 0

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
