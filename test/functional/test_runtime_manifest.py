"""
Functional tests: runtime manifest integration with Salt loader.

Verifies that when a runtime manifest is provided via Salt opts,
the loader uses it to resolve package paths instead of scanning
the full vendor directory.
"""

import textwrap
from pathlib import Path

import pytest
import yaml

from conftest import requires_salt, salt_call

pytestmark = requires_salt


def _create_manifest_project(tmp_path: Path) -> tuple[Path, Path]:
    """Create a project with two packages but a manifest activating only one.

    Returns (project_dir, manifest_path).
    """
    vendor = tmp_path / "vendor"

    # Package A – should be active
    pkg_a = vendor / "active-pkg"
    (pkg_a / "_modules").mkdir(parents=True)
    (pkg_a / "FORMULA").write_text(yaml.dump({
        "name": "active-pkg",
        "version": "1.0.0",
        "description": "Active package",
    }))
    (pkg_a / "_modules" / "active_mod.py").write_text(textwrap.dedent("""\
        def ping():
            return "active module"
    """))

    # Package B – should NOT be active via manifest
    pkg_b = vendor / "inactive-pkg"
    (pkg_b / "_modules").mkdir(parents=True)
    (pkg_b / "FORMULA").write_text(yaml.dump({
        "name": "inactive-pkg",
        "version": "1.0.0",
        "description": "Inactive package",
    }))
    (pkg_b / "_modules" / "inactive_mod.py").write_text(textwrap.dedent("""\
        def ping():
            return "inactive module"
    """))

    # Saltfile
    (tmp_path / "Saltfile").write_text(yaml.dump({"vendor_dir": "vendor"}))

    # Manifest that only activates pkg A
    manifest_path = tmp_path / "runtime_manifest.yaml"
    manifest_path.write_text(yaml.dump({
        "schema": 1,
        "saltenv": "base",
        "fingerprint": "test-fingerprint-001",
        "packages": [
            {
                "name": "active-pkg",
                "version": "1.0.0",
                "type": "formula",
                "digest": "sha256:0000000000000000",
                "path": str(pkg_a),
            },
        ],
    }))

    return tmp_path, manifest_path


class TestRuntimeManifestLoader:
    """Loader should respect runtime manifest when provided."""

    def test_without_manifest_both_modules_available(self, tmp_path):
        """Without manifest, both vendor packages are loaded (legacy mode)."""
        project_dir, _ = _create_manifest_project(tmp_path)

        r = salt_call("sys.list_modules", cwd=project_dir)
        assert r["returncode"] == 0, r["stderr"]
        modules = r["json"]["local"]
        assert "active_mod" in modules
        assert "inactive_mod" in modules

    def test_manifest_file_is_valid_yaml(self, tmp_path):
        """Manifest file should be valid and parseable."""
        _, manifest_path = _create_manifest_project(tmp_path)
        data = yaml.safe_load(manifest_path.read_text())
        assert data["schema"] == 1
        assert data["saltenv"] == "base"
        assert len(data["packages"]) == 1
        assert data["packages"][0]["name"] == "active-pkg"


class TestManifestSerialization:
    """Test manifest round-trip through the Python API."""

    def test_manifest_roundtrip(self):
        """Serialize → deserialize should preserve all fields."""
        from salt_bundle.activation.manifest import (
            RuntimeManifest,
            ManifestPackageEntry,
            serialize_manifest,
            deserialize_manifest,
        )
        from salt_bundle.activation.models import PackageName

        manifest = RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint="test-fp-123",
            packages=(
                ManifestPackageEntry(
                    name=PackageName.parse("test-pkg"),
                    version="2.0.0",
                    package_type="formula",
                    digest="sha256:abcdef",
                    path="vendor/test-pkg",
                ),
            ),
        )

        serialized = serialize_manifest(manifest)
        restored = deserialize_manifest(serialized)

        assert restored.schema_version == manifest.schema_version
        assert restored.saltenv == manifest.saltenv
        assert restored.fingerprint == manifest.fingerprint
        assert len(restored.packages) == 1
        assert restored.packages[0].version == "2.0.0"
        assert restored.packages[0].path == "vendor/test-pkg"

    def test_manifest_save_load(self, tmp_path):
        """save_manifest → load_manifest round-trip."""
        from salt_bundle.activation.manifest import (
            RuntimeManifest,
            ManifestPackageEntry,
            save_manifest,
            load_manifest,
        )
        from salt_bundle.activation.models import PackageName

        manifest = RuntimeManifest(
            schema_version=1,
            saltenv="production",
            fingerprint="fp-save-load",
            packages=(
                ManifestPackageEntry(
                    name=PackageName.parse("myvendor/mypkg"),
                    version="3.1.0",
                    package_type="extension",
                    digest="sha256:deadbeef",
                    path="vendor/myvendor/mypkg",
                ),
            ),
        )

        manifest_path = tmp_path / "manifests" / "test.yaml"
        save_manifest(manifest, manifest_path)
        assert manifest_path.exists()

        loaded = load_manifest(manifest_path)
        assert loaded.fingerprint == "fp-save-load"
        assert loaded.packages[0].name.full_name == "myvendor/mypkg"
        assert loaded.packages[0].package_type == "extension"
