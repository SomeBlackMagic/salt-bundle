"""Tests for parsing ``top_bundle.sls`` activation maps."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


class TestTopBundleParser(unittest.TestCase):
    def _parser_module(self):
        spec = importlib.util.find_spec("salt_bundle.activation.parser")
        self.assertIsNotNone(spec, "top_bundle parser module must exist")

        from salt_bundle.activation import parser

        return parser

    def test_parse_returns_rules_for_a_single_environment(self) -> None:
        parser = self._parser_module()

        top_bundle = parser.parse_top_bundle(
            """
            base:
              'web-*':
                - acme/nginx
                - community/linux-base
            """
        )

        rule = top_bundle.environments["base"].rules[0]
        self.assertEqual(rule.target_expr, "web-*")
        self.assertEqual(
            [str(package) for package in rule.packages],
            ["acme/nginx", "community/linux-base"],
        )

    def test_parse_keeps_environments_separate(self) -> None:
        parser = self._parser_module()

        top_bundle = parser.parse_top_bundle(
            """
            base:
              'web-*': [acme/nginx]
            dev:
              'db-*': [community/postgresql]
            """
        )

        self.assertEqual(set(top_bundle.environments), {"base", "dev"})
        self.assertEqual(
            str(top_bundle.environments["dev"].rules[0].packages[0]),
            "community/postgresql",
        )

    def test_parse_allows_configuration_without_base_environment(self) -> None:
        parser = self._parser_module()

        top_bundle = parser.parse_top_bundle("dev: {}")

        self.assertEqual(top_bundle.environments["dev"].rules, [])

    def test_parse_rejects_invalid_yaml(self) -> None:
        parser = self._parser_module()

        with self.assertRaises(parser.BundleTopSyntaxError):
            parser.parse_top_bundle("base: [")

    def test_parse_rejects_non_mapping_root(self) -> None:
        parser = self._parser_module()

        with self.assertRaises(parser.BundleTopSyntaxError):
            parser.parse_top_bundle("- acme/nginx")

    def test_parse_rejects_package_name_without_vendor(self) -> None:
        parser = self._parser_module()

        with self.assertRaises(parser.BundleTopSyntaxError):
            parser.parse_top_bundle("base: {'web-*': [nginx]}")

    def test_parse_rejects_duplicate_packages_in_a_rule(self) -> None:
        parser = self._parser_module()

        with self.assertRaises(parser.BundleTopSyntaxError):
            parser.parse_top_bundle("base: {'web-*': [acme/nginx, acme/nginx]}")

    def test_parse_rejects_duplicate_target_expressions(self) -> None:
        parser = self._parser_module()

        with self.assertRaises(parser.BundleTopSyntaxError):
            parser.parse_top_bundle(
                """
                base:
                  'web-*': [acme/nginx]
                  'web-*': [community/linux-base]
                """
            )

    def test_parse_empty_document_as_an_empty_top_bundle(self) -> None:
        parser = self._parser_module()

        top_bundle = parser.parse_top_bundle("")

        self.assertEqual(top_bundle.environments, {})

    def test_parse_allows_empty_environment(self) -> None:
        parser = self._parser_module()

        top_bundle = parser.parse_top_bundle("base: {}")

        self.assertEqual(top_bundle.environments["base"].rules, [])

    def test_parse_rejects_integer_package_name(self) -> None:
        parser = self._parser_module()

        with self.assertRaises(parser.BundleTopSyntaxError):
            parser.parse_top_bundle("base: {'web-*': [acme/nginx, 42]}")

    def test_parse_rejects_boolean_package_name(self) -> None:
        parser = self._parser_module()

        with self.assertRaises(parser.BundleTopSyntaxError):
            parser.parse_top_bundle("base: {'web-*': [true]}")

    def test_load_reads_and_parses_top_bundle_file(self) -> None:
        parser = self._parser_module()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "top_bundle.sls"
            path.write_text("base: {'web-*': [acme/nginx]}", encoding="utf-8")

            top_bundle = parser.load_top_bundle(path)

        self.assertEqual(
            str(top_bundle.environments["base"].rules[0].packages[0]),
            "acme/nginx",
        )
