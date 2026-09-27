"""Tests for grouping targets that share an activated runtime."""

import importlib.util
from pathlib import Path
import unittest

from salt_bundle.activation.errors import PackageNotMaterializedError
from salt_bundle.activation.models import ActivePackageSet, PackageName, ResolvedPackage


class RecordingResolver:
    """A resolver fake that records the public calls made by the grouping API."""

    def __init__(self, resolved_sets: dict[str, ActivePackageSet]) -> None:
        self.resolved_sets = resolved_sets
        self.calls: list[tuple[str, str]] = []

    def resolve(self, target: str, *, saltenv: str = "base") -> ActivePackageSet:
        self.calls.append((target, saltenv))
        return self.resolved_sets[target]


class TestRuntimeGrouping(unittest.TestCase):
    """Specify grouping by activated runtime manifest fingerprint."""

    @staticmethod
    def _grouping_module():
        spec = importlib.util.find_spec("salt_bundle.runtime.grouping")
        assert spec is not None, "runtime must provide a target grouping module"

        from salt_bundle.runtime import grouping

        return grouping

    @staticmethod
    def _active_set(target: str, fingerprint: str) -> ActivePackageSet:
        package = ResolvedPackage(
            name=PackageName.parse("acme/nginx"),
            version="1.2.0",
            package_type="formula",
            path=Path("vendor/acme/nginx"),
            digest="sha256:nginx",
        )
        return ActivePackageSet(
            target=target,
            saltenv="base",
            packages=(package,),
            fingerprint=fingerprint,
        )

    def test_groups_targets_with_an_identical_fingerprint(self) -> None:
        grouping = self._grouping_module()
        resolver = RecordingResolver(
            {
                "web-01": self._active_set("web-01", "sha256:shared"),
                "web-02": self._active_set("web-02", "sha256:shared"),
            }
        )

        groups = grouping.group_targets_by_runtime(
            ["web-02", "web-01"], resolver, saltenv="prod"
        )

        self.assertEqual(list(groups), ["sha256:shared"])
        self.assertEqual(groups["sha256:shared"].fingerprint, "sha256:shared")
        self.assertEqual(groups["sha256:shared"].targets, ["web-01", "web-02"])
        self.assertEqual(
            groups["sha256:shared"].manifest.fingerprint, "sha256:shared"
        )
        self.assertEqual(resolver.calls, [("web-02", "prod"), ("web-01", "prod")])

    def test_keeps_different_package_sets_in_separate_groups(self) -> None:
        grouping = self._grouping_module()
        resolver = RecordingResolver(
            {
                "web-01": self._active_set("web-01", "sha256:nginx"),
                "db-01": self._active_set("db-01", "sha256:postgres"),
                "db-02": self._active_set("db-02", "sha256:postgres"),
            }
        )

        groups = grouping.group_targets_by_runtime(
            ["db-02", "web-01", "db-01"], resolver
        )

        self.assertEqual(set(groups), {"sha256:nginx", "sha256:postgres"})
        self.assertEqual(groups["sha256:nginx"].targets, ["web-01"])
        self.assertEqual(groups["sha256:postgres"].targets, ["db-01", "db-02"])

    def test_returns_no_groups_when_no_targets_are_requested(self) -> None:
        grouping = self._grouping_module()
        resolver = RecordingResolver({})

        self.assertEqual(grouping.group_targets_by_runtime([], resolver), {})
        self.assertEqual(resolver.calls, [])

    def test_propagates_a_target_resolution_error_instead_of_skipping_it(self) -> None:
        grouping = self._grouping_module()

        class FailingResolver:
            def resolve(self, target: str, *, saltenv: str = "base") -> ActivePackageSet:
                raise PackageNotMaterializedError("acme/nginx", "vendor/acme/nginx")

        with self.assertRaises(PackageNotMaterializedError):
            grouping.group_targets_by_runtime(["web-01"], FailingResolver())

