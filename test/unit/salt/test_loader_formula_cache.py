"""Regression tests for _get_formula_paths caching consistency (bugfix #010)."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from salt_bundle.salt import loader


@pytest.fixture(autouse=True)
def _clear_formula_cache():
    """Reset formula cache before each test."""
    original = loader._CACHE['formulas']
    loader._CACHE['formulas'] = None
    yield
    loader._CACHE['formulas'] = original


@pytest.fixture
def project_dir(tmp_path):
    return tmp_path


class TestGetFormulaPathsCaching:
    """Verify _get_formula_paths handles empty results consistently."""

    def test_returns_empty_list_when_vendor_dir_does_not_exist(
        self, project_dir,
    ):
        result = loader._get_formula_paths(project_dir, "vendor")

        assert result == []

    def test_discovers_formulas_after_vendor_dir_appears(
        self, project_dir,
    ):
        """When vendor dir initially missing, formulas added later must be found."""
        # First call — vendor does not exist
        loader._get_formula_paths(project_dir, "vendor")

        # Vendor dir appears with a formula
        vendor = project_dir / "vendor"
        formula = vendor / "my-formula"
        formula.mkdir(parents=True)
        (formula / "init.sls").touch()

        with patch.object(
            loader, "discover_package_paths", return_value=[formula],
        ) as mock_discover:
            result = loader._get_formula_paths(project_dir, "vendor")

        assert result == [formula]
        mock_discover.assert_called_once()

    def test_discovers_formulas_after_empty_vendor_dir_is_populated(
        self, project_dir,
    ):
        """When vendor dir exists but is empty, formulas added later must be found."""
        vendor = project_dir / "vendor"
        vendor.mkdir()

        # First call — vendor exists but discover returns []
        with patch.object(
            loader, "discover_package_paths", return_value=[],
        ):
            first_result = loader._get_formula_paths(project_dir, "vendor")

        assert first_result == []

        # Formula installed later
        formula = vendor / "my-formula"
        formula.mkdir()

        with patch.object(
            loader, "discover_package_paths", return_value=[formula],
        ) as mock_discover:
            second_result = loader._get_formula_paths(project_dir, "vendor")

        assert second_result == [formula]
        mock_discover.assert_called_once()

    def test_caches_non_empty_result(self, project_dir):
        """When formulas are found, subsequent calls return cached result."""
        vendor = project_dir / "vendor"
        formula = vendor / "my-formula"
        formula.mkdir(parents=True)

        with patch.object(
            loader, "discover_package_paths", return_value=[formula],
        ) as mock_discover:
            first = loader._get_formula_paths(project_dir, "vendor")
            second = loader._get_formula_paths(project_dir, "vendor")

        assert first == [formula]
        assert second == [formula]
        # discover_package_paths called only once due to caching
        mock_discover.assert_called_once()
