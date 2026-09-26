"""Tests for activation domain models."""

import unittest

from salt_bundle.activation.models import PackageName


class TestPackageName(unittest.TestCase):
    def test_parse_returns_vendor_and_package_parts(self) -> None:
        package_name = PackageName.parse("acme/nginx")

        self.assertEqual(package_name.vendor, "acme")
        self.assertEqual(package_name.package, "nginx")
        self.assertEqual(package_name.full_name, "acme/nginx")
        self.assertEqual(str(package_name), "acme/nginx")

    def test_parse_rejects_invalid_package_names(self) -> None:
        invalid_names = (
            "nginx",
            "a/b/c",
            "/nginx",
            "acme/",
            "Acme/nginx",
            "acme/Nginx",
            "-acme/nginx",
            "acme-/nginx",
            "acme/-nginx",
            "acme/nginx-",
            "acme/nginx_module",
        )

        for package_name in invalid_names:
            with self.subTest(package_name=package_name):
                with self.assertRaises(ValueError):
                    PackageName.parse(package_name)

    def test_package_names_compare_by_vendor_and_package(self) -> None:
        self.assertEqual(PackageName.parse("acme/nginx"), PackageName.parse("acme/nginx"))
        self.assertNotEqual(PackageName.parse("acme/nginx"), PackageName.parse("contoso/nginx"))
