"""
Functional tests: executing custom modules and states through Salt.

Verifies that vendor-provided modules/states can actually run,
not just be discovered.
"""

import pytest

from conftest import requires_salt, salt_call, salt_call_raw

pytestmark = requires_salt


class TestModuleExecution:
    """Call functions from vendor-provided execution modules."""

    def test_module_ping(self, project_dir):
        """test_module.ping should return 'module loaded'."""
        r = salt_call("test_module.ping", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "module loaded"

    def test_module_not_found_returns_error(self, project_dir):
        """Calling a non-existent module should fail gracefully."""
        r = salt_call("nonexistent_module.ping", cwd=project_dir)
        assert r["returncode"] != 0 or (
            r["json"] and "is not available" in str(r["json"])
        )


class TestStateExecution:
    """Apply vendor-provided states through Salt."""

    def test_state_present(self, project_dir):
        """state.single test_state.present should succeed."""
        r = salt_call(
            "state.single", "test_state.present", "name=functional_test",
            cwd=project_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        # state.single returns {"state_id": {…}}
        state_result = list(result.values())[0]
        assert state_result["result"] is True
        assert state_result["comment"] == "state loaded"

    def test_state_with_different_name(self, project_dir):
        """Verify state passes 'name' argument correctly."""
        r = salt_call(
            "state.single", "test_state.present", "name=another_test",
            cwd=project_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        state_result = list(result.values())[0]
        assert state_result["name"] == "another_test"
        assert state_result["result"] is True


class TestCustomOutputter:
    """Verify custom outputter from vendor package works."""

    def test_custom_outputter(self, project_dir):
        """salt-call --out=test_output should use vendor outputter."""
        r = salt_call_raw(
            "test_module.ping", "--out=test_output",
            cwd=project_dir,
        )
        assert r.returncode == 0, r.stderr
        assert "output loaded" in r.stdout


class TestGrainExecution:
    """Verify custom grains are actually computed and accessible."""

    def test_grain_value(self, project_dir):
        """Custom grain test_grain should have value 'loaded'."""
        r = salt_call("grains.get", "test_grain", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "loaded"

    def test_grain_in_items(self, project_dir):
        """Custom grain should appear in grains.items output."""
        r = salt_call("grains.item", "test_grain", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"]["test_grain"] == "loaded"
