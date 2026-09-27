"""Tests for target-aware package activation resolution."""

from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation.errors import (
    ExplicitConflictError,
    NamespaceCollisionError,
    PackageNotMaterializedError,
    UnknownPackageError,
)
from salt_bundle.activation.parser import parse_top_bundle
from salt_bundle.activation.resolver import ActivationResolver
from salt_bundle.dependencies.lock_models import LockFile, LockedDependency


class TestActivationResolver(unittest.TestCase):
    """Specify resolution from activation rules, lock data, and vendor content."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.vendor_root = Path(self.temporary_directory.name) / "vendor"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def _lock_entry(
        *,
        package_type: str = "formula",
        dependencies: dict[str, str] | None = None,
    ) -> LockedDependency:
        return LockedDependency(
            version="1.0.0",
            repository="example",
            url="https://example.invalid/package",
            digest="sha256:" + "0" * 64,
            type=package_type,
            dependencies=dependencies or {},
        )

    def _resolver(
        self, content: str, dependencies: dict[str, LockedDependency]
    ) -> ActivationResolver:
        return ActivationResolver(
            parse_top_bundle(content), LockFile(dependencies=dependencies), self.vendor_root
        )

    def _materialize(self, package_name: str) -> Path:
        path = self.vendor_root / package_name
        path.mkdir(parents=True)
        return path

    def test_resolves_direct_package_for_matching_target(self) -> None:
        self._materialize("acme/nginx")
        resolver = self._resolver(
            "base: {'web-*': [acme/nginx]}",
            {"acme/nginx": self._lock_entry()},
        )

        active_set = resolver.resolve("web-01")

        self.assertEqual(
            [package.name.full_name for package in active_set.packages], ["acme/nginx"]
        )
        self.assertEqual(active_set.target, "web-01")
        self.assertEqual(active_set.saltenv, "base")

    def test_includes_transitive_dependencies_after_direct_packages(self) -> None:
        self._materialize("acme/nginx")
        self._materialize("community/linux-base")
        resolver = self._resolver(
            "base: {'web-*': [acme/nginx]}",
            {
                "acme/nginx": self._lock_entry(
                    dependencies={"community/linux-base": ">=1.0"}
                ),
                "community/linux-base": self._lock_entry(),
            },
        )

        active_set = resolver.resolve("web-01")

        self.assertEqual(
            [package.name.full_name for package in active_set.packages],
            ["acme/nginx", "community/linux-base"],
        )

    def test_rejects_a_direct_package_missing_from_lock_data(self) -> None:
        resolver = self._resolver("base: {'web-*': [acme/nginx]}", {})

        with self.assertRaises(UnknownPackageError):
            resolver.resolve("web-01")

    def test_rejects_a_transitive_package_missing_from_lock_data(self) -> None:
        self._materialize("acme/nginx")
        resolver = self._resolver(
            "base: {'web-*': [acme/nginx]}",
            {
                "acme/nginx": self._lock_entry(
                    dependencies={"community/linux-base": ">=1.0"}
                )
            },
        )

        with self.assertRaises(UnknownPackageError):
            resolver.resolve("web-01")

    def test_rejects_a_locked_package_that_is_not_materialized(self) -> None:
        resolver = self._resolver(
            "base: {'web-*': [acme/nginx]}",
            {"acme/nginx": self._lock_entry()},
        )

        with self.assertRaises(PackageNotMaterializedError):
            resolver.resolve("web-01")

    def test_returns_an_empty_package_set_when_no_rule_matches(self) -> None:
        resolver = self._resolver(
            "base: {'web-*': [acme/nginx]}",
            {"acme/nginx": self._lock_entry()},
        )

        active_set = resolver.resolve("db-01")

        self.assertEqual(active_set.packages, ())

    def test_keeps_environment_resolution_and_fingerprint_deterministic(self) -> None:
        self._materialize("acme/nginx")
        self._materialize("community/postgresql")
        resolver = self._resolver(
            """
            base:
              'web-*': [acme/nginx]
            production:
              'web-*': [community/postgresql]
            """,
            {
                "acme/nginx": self._lock_entry(),
                "community/postgresql": self._lock_entry(),
            },
        )

        first = resolver.resolve("web-01", saltenv="production")
        second = resolver.resolve("web-01", saltenv="production")

        self.assertEqual(
            [package.name.full_name for package in first.packages],
            ["community/postgresql"],
        )
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_rejects_active_packages_with_an_explicit_conflict(self) -> None:
        first = self._materialize("acme/nginx")
        second = self._materialize("contoso/nginx")
        (first / "EXTENSION").write_text(
            "name: acme/nginx\nversion: 1.0.0\nconflicts:\n  - name: contoso/nginx\n",
            encoding="utf-8",
        )
        (second / "EXTENSION").write_text(
            "name: contoso/nginx\nversion: 1.0.0\n",
            encoding="utf-8",
        )
        resolver = self._resolver(
            "base: {'web-*': [acme/nginx, contoso/nginx]}",
            {
                "acme/nginx": self._lock_entry(package_type="extension"),
                "contoso/nginx": self._lock_entry(package_type="extension"),
            },
        )

        with self.assertRaises(ExplicitConflictError):
            resolver.resolve("web-01")

    def test_rejects_active_packages_that_collide_in_a_loader_namespace(self) -> None:
        first = self._materialize("acme/nginx")
        second = self._materialize("contoso/nginx")
        for package in (first, second):
            module_dir = package / "_modules"
            module_dir.mkdir()
            (module_dir / "nginx.py").write_text("def present(): pass\n", encoding="utf-8")
        resolver = self._resolver(
            "base: {'web-*': [acme/nginx, contoso/nginx]}",
            {
                "acme/nginx": self._lock_entry(),
                "contoso/nginx": self._lock_entry(),
            },
        )

        with self.assertRaises(NamespaceCollisionError):
            resolver.resolve("web-01")
