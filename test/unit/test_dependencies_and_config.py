import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from salt_bundle.config import add_user_repository, load_user_config
from salt_bundle.dependencies import index
from salt_bundle.dependencies.index_models import Index, IndexEntry
from salt_bundle.dependencies.lock_models import LockFile
from salt_bundle.dependencies.lockfile import add_locked_dependency, remove_locked_dependency
from salt_bundle.dependencies.resolver import matches_constraint, parse_version, resolve_version
from salt_bundle.packaging.archives import pack_formula


class TestDependenciesAndConfig(unittest.TestCase):
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

    def test_local_index_round_trip_and_package_download(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository_dir = Path(temporary_directory)
            package_dir = repository_dir / "source"
            package_dir.mkdir()
            (package_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
            (package_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
            archive_path = pack_formula(package_dir, repository_dir)
            generated_index = index.generate_index(repository_dir)
            index.save_index(generated_index, repository_dir)
            fetched_index = index.fetch_index(str(repository_dir))
            entry = fetched_index.packages["example"][0]
            with patch("salt_bundle.dependencies.index.get_cache_dir", return_value=repository_dir / "cache"):
                downloaded = index.download_package(entry.url, str(repository_dir), entry.digest)
            self.assertEqual(downloaded.read_bytes(), archive_path.read_bytes())

    def test_user_config_and_lock_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": temporary_directory}, clear=False):
                add_user_repository("main", "https://example.test/index")
                self.assertEqual(load_user_config().repositories[0].name, "main")
                with self.assertRaises(ValueError):
                    add_user_repository("main", "https://duplicate.test/index")

        lock = LockFile()
        add_locked_dependency(lock, "example", "1.0.0", "source", "example.tgz", "sha256:abc")
        self.assertIn("example", lock.dependencies)
        remove_locked_dependency(lock, "example")
        self.assertEqual(lock.dependencies, {})
