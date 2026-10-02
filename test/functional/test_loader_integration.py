"""
Functional tests: Salt loader discovers modules from vendor packages.

Verifies that salt-bundle's entry-point hooks (module_dirs, states_dirs, …)
make Salt see every supported namespace directory.
"""

import pytest

from conftest import requires_salt, salt_call

pytestmark = requires_salt


# -------------------------------------------------------------------
# sys.list_* tests – Salt sees modules provided by vendor packages
# -------------------------------------------------------------------

class TestModuleDiscovery:
    """Verify that Salt discovers custom modules from vendor/foo."""

    def test_custom_module_listed(self, project_dir):
        """salt-call sys.list_modules must include test_module."""
        r = salt_call("sys.list_modules", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        modules = r["json"]["local"]
        assert "test_module" in modules

    def test_custom_state_listed(self, project_dir):
        """salt-call sys.list_state_modules must include test_state."""
        r = salt_call("sys.list_state_modules", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        states = r["json"]["local"]
        assert "test_state" in states

    def test_custom_grain_available(self, project_dir):
        """Custom grain from vendor/foo/_grains should be loaded."""
        r = salt_call("grains.get", "test_grain", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "loaded"

    def test_custom_renderer_listed(self, project_dir):
        """salt-call sys.list_renderers must include test_renderer."""
        r = salt_call("sys.list_renderers", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        renderers = r["json"]["local"]
        assert "test_renderer" in renderers

    def test_custom_returner_listed(self, project_dir):
        """salt-call sys.list_returners must include test_returner."""
        r = salt_call("sys.list_returners", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        returners = r["json"]["local"]
        assert "test_returner" in returners

    def test_custom_beacon_listed(self, project_dir):
        """salt-call sys.list_beacons must include test_beacon."""
        r = salt_call("sys.list_beacons", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        beacons = r["json"]["local"]
        assert "test_beacon" in beacons

    def test_custom_utils_listed(self, project_dir):
        """salt-call sys.list_utils must include test_utils."""
        r = salt_call("sys.list_utils", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        # sys.list_utils returns "module.function" format
        utils_names = r["json"]["local"]
        assert any("test_utils" in u for u in utils_names)

    def test_custom_serializer_listed(self, project_dir):
        """salt-call sys.list_serializers must include test_serializer."""
        r = salt_call("sys.list_serializers", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        serializers = r["json"]["local"]
        assert "test_serializer" in serializers

    def test_custom_executor_listed(self, project_dir):
        """salt-call sys.list_executors must include test_executor."""
        r = salt_call("sys.list_executors", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        executors = r["json"]["local"]
        assert "test_executor" in executors

    def test_custom_matcher_listed(self, project_dir):
        """salt-call sys.list_matchers must include test_matcher."""
        r = salt_call("sys.list_matchers", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        matchers = r["json"]["local"]
        assert "test_matcher" in matchers


class TestNoVendorDir:
    """When there are no packages in vendor, Salt should still work."""

    def test_salt_works_without_vendor(self, tmp_path):
        """salt-call should work even when Saltfile points to empty vendor."""
        saltfile = tmp_path / "Saltfile"
        saltfile.write_text("vendor_dir: vendor\n")
        (tmp_path / "vendor").mkdir()

        r = salt_call("test.ping", cwd=tmp_path)
        assert r["returncode"] == 0
        assert r["json"]["local"] is True

    def test_salt_works_without_saltfile(self, tmp_path):
        """salt-call should work when there is no Saltfile at all."""
        r = salt_call("test.ping", cwd=tmp_path)
        assert r["returncode"] == 0
        assert r["json"]["local"] is True
