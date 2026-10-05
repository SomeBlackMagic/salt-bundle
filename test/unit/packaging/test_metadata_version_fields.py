"""Tests for Salt version fields in package metadata."""

import unittest

from salt_bundle.packaging.extensions import ExtensionMeta
from salt_bundle.packaging.models import PackageMeta


class TestMetadataSaltVersionFields(unittest.TestCase):
    def test_formula_normalizes_numeric_salt_versions_to_strings(self) -> None:
        metadata = PackageMeta(
            name="acme/nginx",
            version="1.0.0",
            minimum_version=3006,
            maximum_version=3009,
        )

        self.assertEqual(metadata.minimum_version, "3006")
        self.assertEqual(metadata.maximum_version, "3009")

    def test_extension_normalizes_numeric_salt_versions_to_strings(self) -> None:
        metadata = ExtensionMeta(
            name="acme/monitoring",
            version="1.0.0",
            minimum_version=3006,
            maximum_version=3009,
        )

        self.assertEqual(metadata.minimum_version, "3006")
        self.assertEqual(metadata.maximum_version, "3009")
