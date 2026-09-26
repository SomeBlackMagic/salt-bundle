"""Tests for activation domain models."""

from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from salt_bundle.activation import models
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


class TestActivationDomainModels(unittest.TestCase):
    def _resolved_package_type(self):
        resolved_package_type = getattr(models, "ResolvedPackage", None)
        self.assertIsNotNone(
            resolved_package_type,
            "activation models must define ResolvedPackage",
        )
        return resolved_package_type

    def _active_package_set_type(self):
        active_package_set_type = getattr(models, "ActivePackageSet", None)
        self.assertIsNotNone(
            active_package_set_type,
            "activation models must define ActivePackageSet",
        )
        return active_package_set_type

    def _compute_fingerprint(self):
        compute_fingerprint = getattr(models, "compute_fingerprint", None)
        self.assertIsNotNone(
            compute_fingerprint,
            "activation models must define compute_fingerprint",
        )
        return compute_fingerprint

    def _resolved_package(
        self,
        name: str = "acme/nginx",
        version: str = "1.2.0",
        digest: str = "sha256:nginx",
    ):
        return self._resolved_package_type()(
            name=PackageName.parse(name),
            version=version,
            package_type="formula",
            path=Path("vendor") / name,
            digest=digest,
        )

    def test_resolved_package_is_immutable_and_keeps_all_attributes(self) -> None:
        package = self._resolved_package()

        self.assertEqual(package.name, PackageName.parse("acme/nginx"))
        self.assertEqual(package.version, "1.2.0")
        self.assertEqual(package.package_type, "formula")
        self.assertEqual(package.path, Path("vendor/acme/nginx"))
        self.assertEqual(package.digest, "sha256:nginx")
        with self.assertRaises(FrozenInstanceError):
            package.version = "2.0.0"

    def test_active_package_set_keeps_packages_as_an_immutable_tuple(self) -> None:
        package = self._resolved_package()
        active_package_set = self._active_package_set_type()(
            target="web-01",
            saltenv="base",
            packages=(package,),
            fingerprint="fingerprint",
        )

        self.assertEqual(active_package_set.packages, (package,))
        self.assertIsInstance(active_package_set.packages, tuple)
        with self.assertRaises(FrozenInstanceError):
            active_package_set.target = "web-02"

    def test_fingerprint_is_stable_for_an_identical_package_set(self) -> None:
        packages = (self._resolved_package(),)

        first = self._compute_fingerprint()(packages, "base")
        second = self._compute_fingerprint()(packages, "base")

        self.assertEqual(first, second)

    def test_fingerprint_changes_when_package_version_digest_or_saltenv_changes(self) -> None:
        compute_fingerprint = self._compute_fingerprint()
        original = self._resolved_package()
        baseline = compute_fingerprint((original,), "base")

        variants = (
            (self._resolved_package(version="1.2.1"), "base"),
            (self._resolved_package(digest="sha256:updated"), "base"),
            (original, "dev"),
        )

        for package, saltenv in variants:
            with self.subTest(package=package, saltenv=saltenv):
                self.assertNotEqual(baseline, compute_fingerprint((package,), saltenv))

    def test_fingerprint_uses_canonical_package_name_order(self) -> None:
        nginx = self._resolved_package("acme/nginx", digest="sha256:nginx")
        linux_base = self._resolved_package(
            "community/linux-base", digest="sha256:linux-base"
        )

        self.assertEqual(
            self._compute_fingerprint()((nginx, linux_base), "base"),
            self._compute_fingerprint()((linux_base, nginx), "base"),
        )

    def test_empty_package_set_has_a_valid_stable_fingerprint(self) -> None:
        fingerprint = self._compute_fingerprint()((), "base")

        self.assertIsInstance(fingerprint, str)
        self.assertEqual(len(fingerprint), 64)
        self.assertEqual(fingerprint, self._compute_fingerprint()((), "base"))

    def test_target_does_not_change_the_fingerprint(self) -> None:
        package = self._resolved_package()
        fingerprint = self._compute_fingerprint()((package,), "base")
        active_package_set_type = self._active_package_set_type()

        web = active_package_set_type("web-01", "base", (package,), fingerprint)
        database = active_package_set_type("db-01", "base", (package,), fingerprint)

        self.assertEqual(web.fingerprint, database.fingerprint)
