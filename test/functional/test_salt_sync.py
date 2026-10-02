"""
Functional tests: Salt module synchronization.

Verifies that Salt's saltutil.sync_* commands correctly synchronize
modules from vendor packages loaded via salt-bundle.
"""

import pytest

from conftest import requires_salt, salt_call

pytestmark = requires_salt


class TestSaltUtilSync:
    """Verify saltutil.sync_* picks up vendor modules."""

    def test_sync_modules(self, project_dir):
        """saltutil.sync_modules should sync vendor _modules."""
        r = salt_call("saltutil.sync_modules", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        # Should include test_module from vendor/foo
        assert any("test_module" in m for m in synced)

    def test_sync_states(self, project_dir):
        """saltutil.sync_states should sync vendor _states."""
        r = salt_call("saltutil.sync_states", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        assert any("test_state" in s for s in synced)

    def test_sync_grains(self, project_dir):
        """saltutil.sync_grains should sync vendor _grains."""
        r = salt_call("saltutil.sync_grains", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        assert any("test_grain" in g for g in synced)

    def test_sync_all(self, project_dir):
        """saltutil.sync_all should sync all module types from vendor."""
        r = salt_call("saltutil.sync_all", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        assert isinstance(result, dict)
        # Should contain keys like 'modules', 'states', 'grains', etc.
        assert "modules" in result
        assert "states" in result
        assert "grains" in result

    def test_sync_returners(self, project_dir):
        """saltutil.sync_returners should sync vendor _returners."""
        r = salt_call("saltutil.sync_returners", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        assert any("test_returner" in s for s in synced)

    def test_sync_output(self, project_dir):
        """saltutil.sync_output should sync vendor _output."""
        r = salt_call("saltutil.sync_output", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        assert any("test_output" in s for s in synced)

    def test_sync_beacons(self, project_dir):
        """saltutil.sync_beacons should sync vendor _beacons."""
        r = salt_call("saltutil.sync_beacons", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        assert any("test_beacon" in s for s in synced)

    def test_sync_utils(self, project_dir):
        """saltutil.sync_utils should sync vendor _utils."""
        r = salt_call("saltutil.sync_utils", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        assert any("test_utils" in s for s in synced)

    def test_sync_renderers(self, project_dir):
        """saltutil.sync_renderers should sync vendor _renderers."""
        r = salt_call("saltutil.sync_renderers", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        synced = r["json"]["local"]
        assert isinstance(synced, list)
        assert any("test_renderer" in s for s in synced)


class TestModuleAvailableAfterSync:
    """After sync, modules should be callable even without loader hook."""

    def test_module_works_after_sync_all(self, project_dir):
        """Module should work after saltutil.sync_all."""
        # First sync
        r = salt_call("saltutil.sync_all", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]

        # Then call module
        r = salt_call("test_module.ping", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "module loaded"

    def test_state_works_after_sync_all(self, project_dir):
        """State should work after saltutil.sync_all."""
        r = salt_call("saltutil.sync_all", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]

        r = salt_call(
            "state.single", "test_state.present", "name=post_sync",
            cwd=project_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        state_result = list(result.values())[0]
        assert state_result["result"] is True
