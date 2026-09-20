from pathlib import Path
import tempfile
import unittest

from salt_bundle.dependencies.saltfile import load_saltfile, save_saltfile
from salt_bundle.dependencies.saltfile_models import SaltfileConfig, SaltfileDependency


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
