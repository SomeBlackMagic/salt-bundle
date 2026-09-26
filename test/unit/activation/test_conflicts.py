"""Tests for runtime conflicts between active packages."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation.models import PackageName, ResolvedPackage
from salt_bundle.packaging.extensions import ExtensionMeta


class TestConflictDetection(unittest.TestCase):
    def _conflicts_module(self):
        spec = importlib.util.find_spec("salt_bundle.activation.conflicts")
        self.assertIsNotNone(
            spec,
            "activation must provide a conflict detection module",
        )

        from salt_bundle.activation import conflicts

        return conflicts

    def _package(self, root: Path, name: str, version: str = "1.0.0") -> ResolvedPackage:
        package_path = root / name
        package_path.mkdir(parents=True)
        return ResolvedPackage(
            name=PackageName.parse(name),
            version=version,
            package_type="extension",
            path=package_path,
            digest=f"sha256:{name}",
        )

    @staticmethod
    def _metadata(name: str, conflicts: list[str] | None = None) -> ExtensionMeta:
        return ExtensionMeta(
            name=name,
            version="1.0.0",
            conflicts=[{"name": conflict} for conflict in conflicts or []],
        )

    def test_detect_conflicts_returns_an_empty_report_when_packages_do_not_conflict(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nginx = self._package(root, "acme/nginx")
            postgres = self._package(root, "community/postgresql")

            report = conflicts.detect_conflicts(
                [nginx, postgres],
                {
                    nginx.name: self._metadata("acme/nginx"),
                    postgres.name: self._metadata("community/postgresql"),
                },
            )

        self.assertFalse(report.has_conflicts)
        self.assertEqual(report.explicit, [])
        self.assertEqual(report.collisions, [])

    def test_detect_conflicts_reports_an_active_declared_explicit_conflict(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nginx = self._package(root, "acme/nginx")
            alternative = self._package(root, "contoso/nginx", "2.1.0")

            report = conflicts.detect_conflicts(
                [nginx, alternative],
                {
                    nginx.name: self._metadata("acme/nginx", ["contoso/nginx"]),
                    alternative.name: self._metadata("contoso/nginx"),
                },
            )

        self.assertEqual(len(report.explicit), 1)
        self.assertEqual(
            {package.name.full_name for package in report.explicit[0].packages},
            {"acme/nginx", "contoso/nginx"},
        )

    def test_detect_conflicts_ignores_a_declared_conflict_when_the_other_package_is_inactive(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            nginx = self._package(Path(directory), "acme/nginx")

            report = conflicts.detect_conflicts(
                [nginx],
                {nginx.name: self._metadata("acme/nginx", ["contoso/nginx"])},
            )

        self.assertFalse(report.has_conflicts)

    def test_detect_conflicts_reports_same_module_file_from_two_packages(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._package(root, "acme/nginx")
            second = self._package(root, "contoso/nginx", "2.1.0")
            (first.path / "_modules").mkdir()
            (second.path / "_modules").mkdir()
            (first.path / "_modules" / "nginx.py").touch()
            (second.path / "_modules" / "nginx.py").touch()

            report = conflicts.detect_conflicts([first, second], {})

        self.assertTrue(report.has_conflicts)
        self.assertEqual(len(report.collisions), 1)
        self.assertEqual(report.collisions[0].path, "_modules/nginx.py")
        self.assertEqual(
            [package.name.full_name for package in report.collisions[0].providers],
            ["acme/nginx", "contoso/nginx"],
        )

    def test_detect_conflicts_reports_state_file_collisions(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._package(root, "acme/first")
            second = self._package(root, "acme/second")
            for package in (first, second):
                (package.path / "_states").mkdir()
                (package.path / "_states" / "service.py").touch()

            report = conflicts.detect_conflicts([first, second], {})

        self.assertEqual(report.collisions[0].path, "_states/service.py")

    def test_detect_conflicts_does_not_treat_same_filename_in_different_namespaces_as_a_collision(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module_package = self._package(root, "acme/module")
            state_package = self._package(root, "acme/state")
            (module_package.path / "_modules").mkdir()
            (state_package.path / "_states").mkdir()
            (module_package.path / "_modules" / "shared.py").touch()
            (state_package.path / "_states" / "shared.py").touch()

            report = conflicts.detect_conflicts([module_package, state_package], {})

        self.assertEqual(report.collisions, [])

    def test_detect_conflicts_ignores_same_ordinary_formula_file(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._package(root, "acme/first")
            second = self._package(root, "acme/second")
            (first.path / "nginx.sls").touch()
            (second.path / "nginx.sls").touch()

            report = conflicts.detect_conflicts([first, second], {})

        self.assertEqual(report.collisions, [])

    def test_detect_conflicts_reports_utility_collisions_and_all_three_providers(self) -> None:
        conflicts = self._conflicts_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packages = [
                self._package(root, "acme/first"),
                self._package(root, "acme/second"),
                self._package(root, "acme/third"),
            ]
            for package in packages:
                (package.path / "_utils").mkdir()
                (package.path / "_utils" / "network.py").touch()

            report = conflicts.detect_conflicts(packages, {})

        self.assertEqual(len(report.collisions), 1)
        self.assertEqual(report.collisions[0].path, "_utils/network.py")
        self.assertEqual(
            [package.name.full_name for package in report.collisions[0].providers],
            ["acme/first", "acme/second", "acme/third"],
        )
