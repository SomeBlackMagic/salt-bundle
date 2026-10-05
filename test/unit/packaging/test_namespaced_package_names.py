"""Regression tests for namespaced package identifiers."""

import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from salt_bundle.activation.models import PackageName
from salt_bundle.dependencies import index
from salt_bundle.dependencies.index_models import Index
from salt_bundle.dependencies.lock_models import LockFile, LockedDependency
from salt_bundle.dependencies.path_source import install_from_path_snapshot
from salt_bundle.dependencies.saltfile_models import SaltfileDependency
from salt_bundle.packaging.archives import pack_extension, pack_formula, validate_package_name
from salt_bundle.packaging.extensions import ExtensionMeta
from salt_bundle.packaging.models import FormulaDependency, PackageMeta


class TestNamespacedPackageNames(unittest.TestCase):
    def test_validator_accepts_valid_namespaced_names(self) -> None:
        for name in ("a/b", "my-org/my-pkg", "acme/salt_formula", "a1/b2"):
            with self.subTest(name=name):
                self.assertTrue(validate_package_name(name))

    def test_validator_rejects_legacy_and_malformed_names(self) -> None:
        for name in (
            "nginx",
            "/nginx",
            "acme/",
            "Acme/nginx",
            "acme/Nginx",
            "acme/nginx/extra",
            "a--b/nginx",
            "acme/nginx--extra",
            "acme/_nginx",
            "acme/nginx_",
        ):
            with self.subTest(name=name):
                self.assertFalse(validate_package_name(name))

    def test_formula_dependencies_require_namespaced_names(self) -> None:
        for model, field in (
            (FormulaDependency, {"name": "nginx"}),
        ):
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValidationError):
                    model(**field)

    def test_legacy_metadata_names_are_allowed_for_fallback_processing(self) -> None:
        formula = PackageMeta(name="nginx", version="1.0.0")
        extension = ExtensionMeta(name="monitoring", version="1.0.0")

        self.assertEqual(formula.name, "nginx")
        self.assertEqual(extension.name, "monitoring")

    def test_saltfile_index_and_lockfile_require_namespaced_keys(self) -> None:
        with self.assertRaises(ValidationError):
            SaltfileDependency(name="nginx")
        with self.assertRaises(ValidationError):
            Index(generated="2026-01-01T00:00:00", packages={"nginx": []})
        with self.assertRaises(ValidationError):
            LockFile(
                dependencies={
                    "nginx": LockedDependency(
                        version="1.0.0",
                        repository="default",
                        url="nginx-1.0.0.tgz",
                        digest="sha256:abc",
                        dependencies={"common": "1.0.0"},
                    )
                }
            )

    def test_activation_accepts_underscore_in_package_part(self) -> None:
        name = PackageName.parse("my-org/my_formula")

        self.assertEqual(name.full_name, "my-org/my_formula")

    def test_pack_formula_uses_unambiguous_namespaced_archive_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            formula_dir = Path(temporary_directory)
            (formula_dir / "FORMULA").write_text(
                "name: acme/nginx\nversion: 1.0.0\n", encoding="utf-8"
            )
            (formula_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            archive = pack_formula(formula_dir)

        self.assertEqual(archive.name, "acme--nginx-1.0.0.tgz")

    def test_path_install_rejects_name_that_differs_from_formula_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_dir = Path(temporary_directory) / "source"
            source_dir.mkdir()
            (source_dir / "FORMULA").write_text(
                "name: acme/nginx\nversion: 1.0.0\n", encoding="utf-8"
            )
            (source_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Package name mismatch"):
                install_from_path_snapshot(
                    source_dir, "other/nginx", Path(temporary_directory) / "vendor"
                )

    def test_legacy_formula_is_indexed_and_installed_in_legacy_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_dir = root / "source"
            source_dir.mkdir()
            (source_dir / "FORMULA").write_text(
                "name: nginx\nversion: 1.0.0\n", encoding="utf-8"
            )
            (source_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            archive = pack_formula(source_dir, root)
            generated_index = index.generate_index(root)
            installed = install_from_path_snapshot(
                source_dir, "legacy/nginx", root / "vendor"
            )

        self.assertEqual(archive.name, "legacy--nginx-1.0.0.tgz")
        self.assertIn("legacy/nginx", generated_index.packages)
        self.assertEqual(installed, root / "vendor" / "legacy" / "nginx")

    def test_legacy_extension_uses_fallback_namespace_in_archive_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            extension_dir = Path(temporary_directory)
            (extension_dir / "EXTENSION").write_text(
                "name: monitoring\nversion: 1.0.0\n", encoding="utf-8"
            )
            (extension_dir / "_modules").mkdir()
            (extension_dir / "_modules" / "monitoring.py").write_text(
                "", encoding="utf-8"
            )

            archive = pack_extension(extension_dir)

        self.assertEqual(archive.name, "legacy--monitoring-1.0.0.tgz")

    def test_documented_formula_uses_namespaced_package_names(self) -> None:
        project_root = Path(__file__).parents[3]
        formula = (project_root / "docs" / "examples" / "FORMULA").read_text(
            encoding="utf-8"
        )

        self.assertIn("name: someblackmagic/k0s", formula)
        self.assertIn("- name: someblackmagic/bar", formula)
