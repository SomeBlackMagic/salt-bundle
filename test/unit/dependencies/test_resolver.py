import unittest

from salt_bundle.dependencies.index_models import IndexEntry
from salt_bundle.dependencies.resolver import matches_constraint, parse_version, resolve_version


class TestResolver(unittest.TestCase):
    def test_version_constraints_and_resolution(self) -> None:
        self.assertEqual(str(parse_version("1.2.3")), "1.2.3")
        self.assertTrue(matches_constraint("1.2.3", "^1.0.0"))
        self.assertTrue(matches_constraint("1.2.3", "~1.2.0"))
        self.assertTrue(matches_constraint("1.2.3", ">=1.0.0,<2.0.0"))
        self.assertTrue(matches_constraint("1.2.3", "1.2.x"))
        self.assertFalse(matches_constraint("2.0.0", "^1.0.0"))
        entries = [
            IndexEntry(version="1.0.0", url="one", digest="sha256:one"),
            IndexEntry(version="1.2.0", url="two", digest="sha256:two"),
        ]
        self.assertEqual(resolve_version("^1.0.0", entries).version, "1.2.0")
        self.assertIsNone(resolve_version("^2.0.0", entries))
