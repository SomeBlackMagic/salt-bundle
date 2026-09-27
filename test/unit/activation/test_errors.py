"""Tests for target-aware activation errors."""

import unittest

from salt_bundle.activation import errors


class TestActivationErrors(unittest.TestCase):
    """Specify the public activation error hierarchy and messages."""

    def test_activation_errors_are_instantiable(self) -> None:
        self.assertTrue(hasattr(errors, "ExplicitConflictError"))
        self.assertTrue(hasattr(errors, "NamespaceCollisionError"))
        activation_errors = [
            errors.ActivationError(),
            errors.BundleTopSyntaxError(),
            errors.UnknownPackageError("acme/nginx"),
            errors.PackageNotMaterializedError("acme/nginx", "/project/vendor/acme/nginx"),
            errors.RuntimeConflictError(),
            errors.ExplicitConflictError("acme/nginx", "contoso/nginx"),
            errors.NamespaceCollisionError("_modules/nginx.py", ["acme/nginx"]),
            errors.RuntimeManifestError(),
        ]

        self.assertEqual(len(activation_errors), 8)

    def test_activation_error_inheritance_is_preserved(self) -> None:
        self.assertTrue(hasattr(errors, "ExplicitConflictError"))
        self.assertTrue(hasattr(errors, "NamespaceCollisionError"))
        self.assertIsInstance(errors.UnknownPackageError("acme/nginx"), errors.ActivationError)
        self.assertIsInstance(
            errors.ExplicitConflictError("acme/nginx", "contoso/nginx"),
            errors.RuntimeConflictError,
        )
        self.assertIsInstance(
            errors.NamespaceCollisionError("_modules/nginx.py", ["acme/nginx"]),
            errors.RuntimeConflictError,
        )

    def test_unknown_package_error_keeps_context_and_formats_message(self) -> None:
        error = errors.UnknownPackageError("acme/nginx", "production")

        self.assertEqual(error.package_name, "acme/nginx")
        self.assertEqual(error.saltenv, "production")
        self.assertEqual(
            str(error),
            "Unknown package 'acme/nginx' in environment 'production'",
        )

    def test_not_materialized_error_keeps_context_and_suggests_install(self) -> None:
        error = errors.PackageNotMaterializedError(
            "acme/nginx", "/project/vendor/acme/nginx"
        )

        self.assertEqual(error.package_name, "acme/nginx")
        self.assertEqual(error.expected_path, "/project/vendor/acme/nginx")
        self.assertIn("acme/nginx", str(error))
        self.assertIn("salt-bundle project install", str(error))

    def test_explicit_conflict_error_includes_both_package_names(self) -> None:
        self.assertTrue(hasattr(errors, "ExplicitConflictError"))
        error = errors.ExplicitConflictError("acme/nginx", "contoso/nginx")

        self.assertIn("acme/nginx", str(error))
        self.assertIn("contoso/nginx", str(error))

    def test_namespace_collision_error_keeps_path_and_lists_all_providers(self) -> None:
        providers = ["acme/nginx", "contoso/nginx", "community/nginx"]
        self.assertTrue(hasattr(errors, "NamespaceCollisionError"))
        error = errors.NamespaceCollisionError("_modules/nginx.py", providers)

        self.assertEqual(error.path, "_modules/nginx.py")
        self.assertIs(error.providers, providers)
        self.assertEqual(
            str(error),
            "_modules/nginx.py is provided by: acme/nginx, contoso/nginx, community/nginx",
        )
