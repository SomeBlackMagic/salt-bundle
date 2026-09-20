import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from salt_bundle.dependencies import index
from salt_bundle.packaging.archives import pack_formula


class TestIndex(unittest.TestCase):
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
