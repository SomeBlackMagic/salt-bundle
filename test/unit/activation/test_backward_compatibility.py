"""Regression tests for projects that do not yet use ``top_bundle.sls``."""

import logging
import tempfile
import unittest
from pathlib import Path

from salt_bundle.activation.parser import parse_top_bundle
from salt_bundle.activation.resolver import ActivationResolver
from salt_bundle.dependencies.lock_models import LockFile, LockedDependency


class TestActivationResolverBackwardCompatibility(unittest.TestCase):
    """Describe legacy global activation and opt-in strict activation."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.vendor_root = Path(self.temporary_directory.name) / "vendor"
        for package_name in ("acme/nginx", "community/linux-base"):
            (self.vendor_root / package_name).mkdir(parents=True)
        self.lock_data = LockFile(
            dependencies={
                "acme/nginx": LockedDependency(
                    version="1.2.0",
                    repository="default",
                    url="nginx.tar.gz",
                    digest="sha256:nginx",
                ),
                "community/linux-base": LockedDependency(
                    version="3.1.4",
                    repository="default",
                    url="linux-base.tar.gz",
                    digest="sha256:linux-base",
                ),
            }
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_missing_top_bundle_uses_all_installed_packages_and_logs_warning(self) -> None:
        resolver = ActivationResolver(
            top_bundle=None,
            lock_data=self.lock_data,
            vendor_root=self.vendor_root,
        )

        with self.assertLogs("salt_bundle.activation.resolver", logging.WARNING) as logs:
            try:
                active_set = resolver.resolve("web-01")
            except AttributeError as error:
                self.fail(f"Missing legacy global activation support: {error}")

        self.assertEqual(
            [package.name.full_name for package in active_set.packages],
            ["acme/nginx", "community/linux-base"],
        )
        self.assertIn(
            "top_bundle.sls not found; using legacy global activation mode",
            logs.output[0],
        )

    def test_present_top_bundle_keeps_target_specific_activation_without_warning(self) -> None:
        resolver = ActivationResolver(
            top_bundle=parse_top_bundle("base:\n  'web-*':\n    - acme/nginx\n"),
            lock_data=self.lock_data,
            vendor_root=self.vendor_root,
        )

        with self.assertNoLogs("salt_bundle.activation.resolver", logging.WARNING):
            active_set = resolver.resolve("web-01")

        self.assertEqual(
            [package.name.full_name for package in active_set.packages], ["acme/nginx"]
        )

    def test_old_lock_without_dependency_edges_resolves_direct_packages(self) -> None:
        resolver = ActivationResolver(
            top_bundle=parse_top_bundle("base:\n  '*':\n    - acme/nginx\n"),
            lock_data=self.lock_data,
            vendor_root=self.vendor_root,
        )

        active_set = resolver.resolve("web-01")

        self.assertEqual(
            [package.name.full_name for package in active_set.packages], ["acme/nginx"]
        )
