"""Tests for target expression matching and package collection."""

import importlib.util
import unittest

from salt_bundle.activation.models import PackageName
from salt_bundle.activation.parser import TopBundleRule


class TestTargetMatcher(unittest.TestCase):
    def _matcher_module(self):
        spec = importlib.util.find_spec("salt_bundle.activation.matcher")
        self.assertIsNotNone(spec, "target matcher module must exist")

        from salt_bundle.activation import matcher

        return matcher

    def test_matches_exact_target_expression(self) -> None:
        matcher = self._matcher_module()

        self.assertTrue(matcher.match_target("server-01", "server-01"))

    def test_does_not_match_different_exact_target_expression(self) -> None:
        matcher = self._matcher_module()

        self.assertFalse(matcher.match_target("server-01", "server-02"))

    def test_asterisk_glob_matches_every_target(self) -> None:
        matcher = self._matcher_module()

        self.assertTrue(matcher.match_target("any.minion-01", "*"))

    def test_glob_matches_only_targets_with_matching_prefix(self) -> None:
        matcher = self._matcher_module()

        self.assertTrue(matcher.match_target("web-01", "web-*"))
        self.assertFalse(matcher.match_target("db-01", "web-*"))

    def test_question_mark_glob_matches_exactly_one_character(self) -> None:
        matcher = self._matcher_module()

        self.assertTrue(matcher.match_target("web-01", "web-??"))
        self.assertFalse(matcher.match_target("web-001", "web-??"))

    def test_matching_is_case_sensitive(self) -> None:
        matcher = self._matcher_module()

        self.assertFalse(matcher.match_target("WEB-01", "web-*"))

    def test_finds_all_matching_rules_in_declaration_order(self) -> None:
        matcher = self._matcher_module()
        base_rule = TopBundleRule(
            target_expr="*", packages=[PackageName.parse("community/linux-base")]
        )
        web_rule = TopBundleRule(
            target_expr="web-*", packages=[PackageName.parse("acme/nginx")]
        )
        database_rule = TopBundleRule(
            target_expr="db-*", packages=[PackageName.parse("community/postgresql")]
        )

        matched_rules = matcher.find_matching_rules(
            "web-01", [base_rule, web_rule, database_rule]
        )

        self.assertEqual(matched_rules, [base_rule, web_rule])

    def test_returns_no_rules_when_target_does_not_match(self) -> None:
        matcher = self._matcher_module()
        rule = TopBundleRule(
            target_expr="web-*", packages=[PackageName.parse("acme/nginx")]
        )

        self.assertEqual(matcher.find_matching_rules("db-01", [rule]), [])

    def test_collects_packages_in_first_occurrence_order(self) -> None:
        matcher = self._matcher_module()
        linux_base = PackageName.parse("community/linux-base")
        nginx = PackageName.parse("acme/nginx")
        rules = [
            TopBundleRule(target_expr="*", packages=[linux_base, nginx]),
            TopBundleRule(target_expr="web-*", packages=[nginx, linux_base]),
        ]

        self.assertEqual(matcher.collect_packages(rules), [linux_base, nginx])
