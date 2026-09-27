from pathlib import Path
import tempfile
import unittest

from salt_bundle.dependencies.saltfile import load_saltfile, save_saltfile
from salt_bundle.dependencies.saltfile_models import (
    RuntimeConfig,
    SaltfileConfig,
    SaltfileDependency,
)


class TestSaltfileConfig(unittest.TestCase):
    def test_save_and_load_saltfile_with_index_sources(self) -> None:
        config = SaltfileConfig(
            vendor_dir="third_party/salt",
            dependencies=[
                SaltfileDependency(
                    name="nginx",
                    version="^2.0.0",
                    source="https://packages.example.test/salt",
                ),
                SaltfileDependency(name="common"),
            ],
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            project_dir = Path(temporary_directory)
            save_saltfile(config, project_dir)

            self.assertTrue((project_dir / "Saltfile").exists())
            self.assertEqual(load_saltfile(project_dir), config)

    def test_runtime_configuration_has_defaults_and_round_trips(self) -> None:
        config = SaltfileConfig(
            runtime={
                "top_bundle_file": "environments/prod.sls",
                "cache_dir": ".runtime-cache",
                "max_workers": 8,
                "require_bundle_top": True,
            }
        )

        self.assertEqual(config.runtime.top_bundle_file, "environments/prod.sls")
        self.assertEqual(config.runtime.cache_dir, ".runtime-cache")
        self.assertEqual(config.runtime.max_workers, 8)
        self.assertTrue(config.runtime.require_bundle_top)

    def test_load_saltfile_without_runtime_uses_runtime_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_dir = Path(temporary_directory)
            (project_dir / "Saltfile").write_text(
                "vendor_dir: vendor\ndependencies: []\n", encoding="utf-8"
            )

            config = load_saltfile(project_dir)

        self.assertEqual(config.runtime, RuntimeConfig())

    def test_load_saltfile_parses_custom_runtime_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_dir = Path(temporary_directory)
            (project_dir / "Saltfile").write_text(
                """runtime:
  top_bundle_file: environments/production.sls
  cache_dir: .salt-bundle/production
  max_workers: 12
  require_bundle_top: true
dependencies:
  - name: acme/nginx
    version: ^1.0.0
""",
                encoding="utf-8",
            )

            config = load_saltfile(project_dir)

        self.assertEqual(config.runtime.top_bundle_file, "environments/production.sls")
        self.assertEqual(config.runtime.cache_dir, ".salt-bundle/production")
        self.assertEqual(config.runtime.max_workers, 12)
        self.assertTrue(config.runtime.require_bundle_top)
        self.assertEqual(config.dependencies[0].name, "acme/nginx")
