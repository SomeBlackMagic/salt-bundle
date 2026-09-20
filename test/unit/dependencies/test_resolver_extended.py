import unittest

from salt_bundle.dependencies.index_models import IndexEntry
from salt_bundle.dependencies.resolver import matches_constraint, parse_version, resolve_version


class TestResolverExtended(unittest.TestCase):
    def test_parse_version_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_version("not-a-version")

    def test_matches_exact_version(self) -> None:
        self.assertTrue(matches_constraint("1.2.3", "1.2.3"))
        self.assertFalse(matches_constraint("1.2.4", "1.2.3"))

    def test_matches_invalid_version_returns_false(self) -> None:
        self.assertFalse(matches_constraint("bad", "^1.0.0"))

    def test_matches_invalid_constraint_returns_false(self) -> None:
        self.assertFalse(matches_constraint("1.0.0", "bad-constraint"))

    def test_caret_major_zero_minor_nonzero(self) -> None:
        # ^0.2.0 should match 0.2.x but not 0.3.x
        self.assertTrue(matches_constraint("0.2.1", "^0.2.0"))
        self.assertFalse(matches_constraint("0.3.0", "^0.2.0"))

    def test_caret_major_zero_minor_zero(self) -> None:
        # ^0.0.3 should match only 0.0.3
        self.assertTrue(matches_constraint("0.0.3", "^0.0.3"))
        self.assertFalse(matches_constraint("0.0.4", "^0.0.3"))

    def test_caret_invalid_base_returns_false(self) -> None:
        self.assertFalse(matches_constraint("1.0.0", "^bad"))

    def test_tilde_invalid_base_returns_false(self) -> None:
        self.assertFalse(matches_constraint("1.0.0", "~bad"))

    def test_wildcard_with_star(self) -> None:
        self.assertTrue(matches_constraint("1.2.3", "1.*.*"))
        self.assertFalse(matches_constraint("2.0.0", "1.*.*"))

    def test_wildcard_invalid_part(self) -> None:
        self.assertFalse(matches_constraint("1.0.0", "abc.x.x"))

    def test_single_comparison_operators(self) -> None:
        self.assertTrue(matches_constraint("2.0.0", ">1.0.0"))
        self.assertFalse(matches_constraint("1.0.0", ">1.0.0"))
        self.assertTrue(matches_constraint("1.0.0", "<=1.0.0"))
        self.assertFalse(matches_constraint("1.0.1", "<=1.0.0"))
        self.assertTrue(matches_constraint("0.9.0", "<1.0.0"))
        self.assertTrue(matches_constraint("1.0.0", "=1.0.0"))
        self.assertFalse(matches_constraint("1.0.1", "=1.0.0"))

    def test_comparison_invalid_version_returns_false(self) -> None:
        self.assertFalse(matches_constraint("1.0.0", ">=bad"))

    def test_no_match_returns_false(self) -> None:
        # A constraint with special chars but no recognized pattern
        self.assertFalse(matches_constraint("1.0.0", ""))

    def test_resolve_version_fallback_sort(self) -> None:
        # This tests the normal path; verifying resolve works with multiple candidates
        entries = [
            IndexEntry(version="1.0.0", url="a", digest="sha256:a"),
            IndexEntry(version="1.1.0", url="b", digest="sha256:b"),
            IndexEntry(version="1.2.0", url="c", digest="sha256:c"),
        ]
        result = resolve_version(">=1.0.0", entries)
        self.assertEqual(result.version, "1.2.0")
