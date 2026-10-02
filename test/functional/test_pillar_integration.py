"""
Functional tests: ext_pillar integration.

Verifies that the saltbundle ext_pillar plugin correctly injects
metadata about installed vendor packages into the pillar.
"""

import pytest

from conftest import requires_salt, salt_call

pytestmark = requires_salt


class TestExtPillar:
    """Verify the saltbundle ext_pillar returns package metadata."""

    def test_pillar_returns_saltbundle_key(self, project_dir):
        """pillar.get saltbundle should return a non-empty dict."""
        r = salt_call("pillar.get", "saltbundle", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        pillar_data = r["json"]["local"]
        assert isinstance(pillar_data, dict), f"Expected dict, got {type(pillar_data)}"
        assert len(pillar_data) > 0, "saltbundle pillar is empty"

    def test_pillar_contains_project_dir(self, project_dir):
        """Pillar should include the project directory path."""
        r = salt_call("pillar.get", "saltbundle:project_dir", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        project = r["json"]["local"]
        assert str(project_dir) in str(project)

    def test_pillar_contains_vendor_dir(self, project_dir):
        """Pillar should include the vendor_dir name."""
        r = salt_call("pillar.get", "saltbundle:vendor_dir", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        assert r["json"]["local"] == "vendor"

    def test_pillar_lists_formulas(self, project_dir):
        """Pillar should list installed formula names."""
        r = salt_call("pillar.get", "saltbundle:formulas", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        formulas = r["json"]["local"]
        assert isinstance(formulas, list)
        assert "foo" in formulas

    def test_pillar_lists_formula_paths(self, project_dir):
        """Pillar should list absolute paths to formula directories."""
        r = salt_call("pillar.get", "saltbundle:formula_paths", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        paths = r["json"]["local"]
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert any("foo" in p for p in paths)

    def test_pillar_with_multiple_packages(self, multi_project_dir):
        """Pillar should list all installed packages."""
        r = salt_call("pillar.get", "saltbundle:formulas", cwd=multi_project_dir)
        assert r["returncode"] == 0, r["stderr"]
        formulas = r["json"]["local"]
        assert "foo" in formulas
        assert "bar" in formulas

    def test_pillar_empty_without_saltfile(self, tmp_path):
        """Without a Saltfile, saltbundle pillar should be empty."""
        r = salt_call("pillar.get", "saltbundle", cwd=tmp_path)
        assert r["returncode"] == 0, r["stderr"]
        pillar_data = r["json"]["local"]
        # Should be empty dict or empty string (no pillar data)
        assert not pillar_data or pillar_data == ""
