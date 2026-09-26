"""Tests for serializable activated package runtime manifests."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation.models import ActivePackageSet, PackageName, ResolvedPackage


class TestRuntimeManifest(unittest.TestCase):
    """Specify the portable runtime manifest contract."""

    def _manifest_module(self):
        spec = importlib.util.find_spec("salt_bundle.activation.manifest")
        self.assertIsNotNone(
            spec,
            "activation must provide a runtime manifest module",
        )

        from salt_bundle.activation import manifest

        return manifest

    @staticmethod
    def _active_package_set() -> ActivePackageSet:
        nginx = ResolvedPackage(
            name=PackageName.parse("acme/nginx"),
            version="1.2.0",
            package_type="formula",
            path=Path("vendor/acme/nginx"),
            digest="sha256:nginx",
        )
        linux_base = ResolvedPackage(
            name=PackageName.parse("community/linux-base"),
            version="3.1.4",
            package_type="extension",
            path=Path("vendor/community/linux-base"),
            digest="sha256:linux-base",
        )
        return ActivePackageSet(
            target="web-01",
            saltenv="base",
            packages=(linux_base, nginx),
            fingerprint="f" * 64,
        )

    def test_build_manifest_copies_exact_active_package_details(self) -> None:
        manifest = self._manifest_module()

        runtime_manifest = manifest.build_manifest(self._active_package_set())

        self.assertEqual(runtime_manifest.schema_version, 1)
        self.assertEqual(runtime_manifest.saltenv, "base")
        self.assertEqual(runtime_manifest.fingerprint, "f" * 64)
        self.assertEqual(
            runtime_manifest.packages,
            (
                manifest.ManifestPackageEntry(
                    name=PackageName.parse("acme/nginx"),
                    version="1.2.0",
                    package_type="formula",
                    digest="sha256:nginx",
                    path="vendor/acme/nginx",
                ),
                manifest.ManifestPackageEntry(
                    name=PackageName.parse("community/linux-base"),
                    version="3.1.4",
                    package_type="extension",
                    digest="sha256:linux-base",
                    path="vendor/community/linux-base",
                ),
            ),
        )

    def test_build_manifest_orders_packages_by_canonical_name(self) -> None:
        manifest = self._manifest_module()

        runtime_manifest = manifest.build_manifest(self._active_package_set())

        self.assertEqual(
            [entry.name.full_name for entry in runtime_manifest.packages],
            ["acme/nginx", "community/linux-base"],
        )

    def test_serialize_and_deserialize_preserve_a_runtime_manifest(self) -> None:
        manifest = self._manifest_module()
        original = manifest.build_manifest(self._active_package_set())

        content = manifest.serialize_manifest(original)
        restored = manifest.deserialize_manifest(content)

        self.assertIn("schema: 1", content)
        self.assertEqual(restored, original)

    def test_deserialize_rejects_invalid_yaml_with_runtime_manifest_error(self) -> None:
        manifest = self._manifest_module()

        with self.assertRaises(manifest.RuntimeManifestError):
            manifest.deserialize_manifest("packages: [unterminated")

    def test_deserialize_rejects_a_missing_required_field(self) -> None:
        manifest = self._manifest_module()

        with self.assertRaises(manifest.RuntimeManifestError):
            manifest.deserialize_manifest(
                "schema: 1\nsaltenv: base\nfingerprint: fingerprint\n"
            )

    def test_deserialize_rejects_an_unknown_schema_version(self) -> None:
        manifest = self._manifest_module()

        with self.assertRaises(manifest.RuntimeManifestError):
            manifest.deserialize_manifest(
                "schema: 2\nsaltenv: base\nfingerprint: fingerprint\npackages: []\n"
            )

    def test_deserialize_rejects_absolute_package_paths(self) -> None:
        manifest = self._manifest_module()

        with self.assertRaises(manifest.RuntimeManifestError):
            manifest.deserialize_manifest(
                "schema: 1\nsaltenv: base\nfingerprint: fingerprint\npackages:\n"
                "  - name: acme/nginx\n    version: 1.2.0\n    type: formula\n"
                "    digest: sha256:nginx\n    path: /tmp/vendor/acme/nginx\n"
            )

    def test_save_and_load_manifest_round_trip_through_a_file(self) -> None:
        manifest = self._manifest_module()
        runtime_manifest = manifest.build_manifest(self._active_package_set())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime" / "manifest.yaml"
            manifest.save_manifest(runtime_manifest, path)
            restored = manifest.load_manifest(path)

            self.assertTrue(path.is_file())
        self.assertEqual(restored, runtime_manifest)
