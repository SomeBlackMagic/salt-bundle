import importlib
from pathlib import Path
import tomllib
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestModuleLayout(unittest.TestCase):
    def test_exposes_capability_packages(self) -> None:
        for module_name in (
            "salt_bundle.packaging.archives",
            "salt_bundle.packaging.types",
            "salt_bundle.dependencies.saltfile",
            "salt_bundle.dependencies.resolver",
            "salt_bundle.storage.vendor",
            "salt_bundle.salt.loader",
        ):
            with self.subTest(module_name=module_name):
                importlib.import_module(module_name)

    def test_salt_entry_points_target_salt_package(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)

        entry_points = project["project"]["entry-points"]
        self.assertTrue((PROJECT_ROOT / project["project"]["readme"]).is_file())
        self.assertEqual(
            entry_points["salt.loader"]["module_dirs"],
            "salt_bundle.salt.loader:module_dirs",
        )
        self.assertEqual(
            entry_points["salt.loader.ext_pillar"]["saltbundle"],
            "salt_bundle.salt.pillar:ext_pillar",
        )

        for group_name in ("salt.loader", "salt.loader.ext_pillar"):
            for target in entry_points[group_name].values():
                module_name, callable_name = target.split(":")
                with self.subTest(target=target):
                    self.assertTrue(callable(getattr(importlib.import_module(module_name), callable_name)))

    def test_requires_minimum_coverage_threshold(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)

        self.assertGreaterEqual(project["tool"]["coverage"]["report"]["fail_under"], 85)
