"""
Functional tests: multi-package and extension layout support.

Verifies that salt-bundle correctly handles:
- Multiple formula packages in vendor
- saltext-style extension packages
- Mixed formula + extension projects
- Two-level vendor trees (vendor/{vendor}/{package})
"""

import pytest

from conftest import requires_salt, salt_call

pytestmark = requires_salt


class TestMultipleFormulas:
    """Multiple formula packages should coexist in vendor."""

    def test_modules_from_first_package(self, multi_project_dir):
        """Modules from foo should be available."""
        r = salt_call("test_module.ping", cwd=multi_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "module loaded"

    def test_grains_from_first_package(self, multi_project_dir):
        """Grains from foo should be loaded."""
        r = salt_call("grains.get", "test_grain", cwd=multi_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "loaded"

    def test_state_from_first_package(self, multi_project_dir):
        """States from foo should be executable."""
        r = salt_call(
            "state.single", "test_state.present", "name=multi_test",
            cwd=multi_project_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        state_result = list(result.values())[0]
        assert state_result["result"] is True

    def test_both_packages_in_pillar(self, multi_project_dir):
        """Both packages should appear in pillar metadata."""
        r = salt_call("pillar.get", "saltbundle:formulas", cwd=multi_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        formulas = r["json"]["local"]
        assert "foo" in formulas
        assert "bar" in formulas


class TestExtensionPackage:
    """saltext-style extension packages should be loaded by Salt."""

    def test_extension_module_discovered(self, extension_project_dir):
        """Extension module should appear in sys.list_modules."""
        r = salt_call("sys.list_modules", cwd=extension_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        modules = r["json"]["local"]
        assert "my_ext_mod" in modules

    def test_extension_module_callable(self, extension_project_dir):
        """Extension module function should be callable."""
        r = salt_call("my_ext_mod.ping", cwd=extension_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "extension module loaded"

    def test_extension_state_discovered(self, extension_project_dir):
        """Extension state should appear in sys.list_state_modules."""
        r = salt_call("sys.list_state_modules", cwd=extension_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        states = r["json"]["local"]
        assert "my_ext_state" in states

    def test_extension_state_executable(self, extension_project_dir):
        """Extension state should be executable."""
        r = salt_call(
            "state.single", "my_ext_state.present", "name=ext_test",
            cwd=extension_project_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        state_result = list(result.values())[0]
        assert state_result["result"] is True
        assert state_result["comment"] == "extension state loaded"


class TestMixedProject:
    """Projects with both formulas and extensions should work."""

    def test_formula_module_available(self, mixed_project_dir):
        """Formula module (test_module) should be available."""
        r = salt_call("test_module.ping", cwd=mixed_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "module loaded"

    def test_extension_module_available(self, mixed_project_dir):
        """Extension module (my_ext_mod) should be available alongside formula."""
        r = salt_call("my_ext_mod.ping", cwd=mixed_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "extension module loaded"

    def test_both_modules_listed(self, mixed_project_dir):
        """Both formula and extension modules should appear in module list."""
        r = salt_call("sys.list_modules", cwd=mixed_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        modules = r["json"]["local"]
        assert "test_module" in modules
        assert "my_ext_mod" in modules

    def test_formula_grains_with_extension(self, mixed_project_dir):
        """Formula grains should work when extension is also present."""
        r = salt_call("grains.get", "test_grain", cwd=mixed_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "loaded"


class TestTwoLevelVendor:
    """Two-level vendor tree: vendor/{vendor_name}/{package_name}."""

    def test_two_level_module_discovered(self, two_level_vendor_dir):
        """Module from vendor/acme/web should be discovered."""
        r = salt_call("sys.list_modules", cwd=two_level_vendor_dir)
        assert r["returncode"] == 0, r["stderr"]
        modules = r["json"]["local"]
        assert "acme_web" in modules

    def test_two_level_module_callable(self, two_level_vendor_dir):
        """Module from two-level vendor should be callable."""
        r = salt_call("acme_web.ping", cwd=two_level_vendor_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "acme-web module loaded"

    def test_two_level_state_executable(self, two_level_vendor_dir):
        """State from two-level vendor should be executable."""
        r = salt_call(
            "state.single", "acme_web.present", "name=two_level_test",
            cwd=two_level_vendor_dir,
        )
        assert r["returncode"] == 0, r["stderr"]
        result = r["json"]["local"]
        state_result = list(result.values())[0]
        assert state_result["result"] is True
        assert state_result["comment"] == "acme-web state loaded"
