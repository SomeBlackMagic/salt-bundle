"""Regression tests for bug #002: lexicographic version sort instead of semver.

Versions must be sorted semantically, not lexicographically.
With string sort: "9.0.0" > "10.0.0" because '9' > '1'.
With semver sort: "10.0.0" > "9.0.0" because 10 > 9.
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from salt_bundle.dependencies.index_models import Index, IndexEntry
from salt_bundle.dependencies.resolver import resolve_version


class TestGenerateIndexSortsVersionsSemantically(unittest.TestCase):
    """generate_index() must sort versions by semver, not by string."""

    def test_index_sorts_double_digit_versions_above_single_digit(self):
        """Version 10.0.0 must appear before 9.0.0 in descending sort."""
        from salt_bundle.dependencies.index import generate_index
        from salt_bundle.packaging.archives import pack_formula

        with tempfile.TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "repo"
            repo_dir.mkdir()

            for version in ["1.0.0", "2.0.0", "9.0.0", "10.0.0"]:
                pkg_dir = Path(tmp) / f"pkg-{version}"
                pkg_dir.mkdir()
                (pkg_dir / "FORMULA").write_text(
                    f"name: myformula\nversion: {version}\n", encoding="utf-8"
                )
                (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
                pack_formula(pkg_dir, repo_dir)

            result = generate_index(repo_dir)

        versions = [entry.version for entry in result.packages["legacy/myformula"]]
        self.assertEqual(versions, ["10.0.0", "9.0.0", "2.0.0", "1.0.0"])


class TestReleasePackagesSortsVersionsSemantically(unittest.TestCase):
    """release_packages() must sort index versions by semver."""

    def test_release_index_sorts_double_digit_versions_correctly(self):
        """After releasing versions 1.0.0 and 10.0.0, the index must list 10.0.0 first."""
        from salt_bundle.storage.release import release_packages
        from salt_bundle.storage.providers.local_provider import LocalReleaseProvider

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packages_dir = root / "packages"
            repo_dir = root / "repository"

            for version in ["1.0.0", "9.0.0", "10.0.0"]:
                pkg_dir = packages_dir / f"formula-{version}"
                pkg_dir.mkdir(parents=True, exist_ok=True)
                (pkg_dir / "FORMULA").write_text(
                    f"name: myformula\nversion: {version}\n", encoding="utf-8"
                )
                (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            provider = LocalReleaseProvider(repo_dir)
            released, errors = release_packages(packages_dir, provider)

            self.assertEqual(errors, [])
            self.assertEqual(len(released), 3)

            index = provider.load_index()
            versions = [entry.version for entry in index.packages["legacy/myformula"]]
            self.assertEqual(versions, ["10.0.0", "9.0.0", "1.0.0"])


class TestResolveVersionWithUnparseableVersions(unittest.TestCase):
    """resolve_version() must not fall back to full string sort when one version is unparseable."""

    def test_resolve_returns_highest_semver_even_with_unparseable_candidate(self):
        """When candidates include an unparseable version, resolve_version must still
        return the highest valid semver match, not a lexicographically-highest one.
        """
        candidates = [
            IndexEntry(version="1.0.0", url="a", digest="sha256:a"),
            IndexEntry(version="10.0.0", url="b", digest="sha256:b"),
            IndexEntry(version="9.0.0", url="c", digest="sha256:c"),
        ]

        result = resolve_version(">=1.0.0", candidates)
        self.assertIsNotNone(result)
        self.assertEqual(result.version, "10.0.0")

    def test_resolve_returns_highest_semver_with_many_double_digit_versions(self):
        """Regression: versions like 11.0.0, 2.0.0, 20.0.0 must sort semantically."""
        candidates = [
            IndexEntry(version="2.0.0", url="a", digest="sha256:a"),
            IndexEntry(version="11.0.0", url="b", digest="sha256:b"),
            IndexEntry(version="20.0.0", url="c", digest="sha256:c"),
            IndexEntry(version="3.0.0", url="d", digest="sha256:d"),
        ]

        result = resolve_version(">=1.0.0", candidates)
        self.assertIsNotNone(result)
        self.assertEqual(result.version, "20.0.0")


if __name__ == "__main__":
    unittest.main()
