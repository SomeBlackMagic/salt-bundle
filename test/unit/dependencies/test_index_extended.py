import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from salt_bundle.dependencies import index
from salt_bundle.dependencies.index_models import Index


class TestIndexExtended(unittest.TestCase):
    def test_generate_index_with_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_dir = Path(tmp)
            pkg_dir = repo_dir / "source"
            pkg_dir.mkdir()
            (pkg_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
            (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            from salt_bundle.packaging.archives import pack_formula
            pack_formula(pkg_dir, repo_dir)

            generated = index.generate_index(repo_dir, base_url="https://example.com/repo")
            entry = generated.packages["example"][0]
            self.assertTrue(entry.url.startswith("https://example.com/repo/"))

    def test_generate_index_nonexistent_dir_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            index.generate_index("/nonexistent/path")

    def test_generate_index_updates_existing_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_dir = Path(tmp)
            pkg_dir = repo_dir / "source"
            pkg_dir.mkdir()
            (pkg_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
            (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            from salt_bundle.packaging.archives import pack_formula
            pack_formula(pkg_dir, repo_dir)

            # Generate index twice - second time updates existing version
            idx1 = index.generate_index(repo_dir)
            index.save_index(idx1, repo_dir)
            idx2 = index.generate_index(repo_dir)
            self.assertEqual(len(idx2.packages["example"]), 1)

    def test_fetch_index_file_scheme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_dir = Path(tmp)
            pkg_dir = repo_dir / "source"
            pkg_dir.mkdir()
            (pkg_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
            (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            from salt_bundle.packaging.archives import pack_formula
            pack_formula(pkg_dir, repo_dir)
            idx = index.generate_index(repo_dir)
            index.save_index(idx, repo_dir)

            fetched = index.fetch_index(f"file://{repo_dir}")
            self.assertIn("example", fetched.packages)

    def test_fetch_index_missing_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                index.fetch_index(tmp)

    def test_fetch_index_unsupported_scheme_raises(self) -> None:
        with self.assertRaises(ValueError):
            index.fetch_index("ftp://example.com/repo")

    def test_download_package_unsupported_scheme_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                index.download_package(
                    "ftp://example.com/pkg.tgz",
                    "ftp://example.com/",
                    "sha256:abc",
                    cache_dir=Path(tmp),
                )

    def test_download_package_cache_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "repo"
            cache_dir = Path(tmp) / "cache"
            cache_dir.mkdir()
            repo_dir.mkdir()

            # Create a package
            pkg_dir = Path(tmp) / "source"
            pkg_dir.mkdir()
            (pkg_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
            (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            from salt_bundle.packaging.archives import pack_formula
            from salt_bundle.utils.hashing import calculate_sha256
            archive = pack_formula(pkg_dir, repo_dir)
            digest = calculate_sha256(archive)

            # First download
            result1 = index.download_package(archive.name, str(repo_dir), digest, cache_dir=cache_dir)
            self.assertTrue(result1.exists())

            # Second download should be cache hit
            result2 = index.download_package(archive.name, str(repo_dir), digest, cache_dir=cache_dir)
            self.assertEqual(result1, result2)

    def test_download_package_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "repo"
            cache_dir = Path(tmp) / "cache"
            cache_dir.mkdir()
            repo_dir.mkdir()

            pkg_dir = Path(tmp) / "source"
            pkg_dir.mkdir()
            (pkg_dir / "FORMULA").write_text("name: example\nversion: 1.0.0\n", encoding="utf-8")
            (pkg_dir / "init.sls").write_text("test: true\n", encoding="utf-8")

            from salt_bundle.packaging.archives import pack_formula
            pack_formula(pkg_dir, repo_dir)

            with self.assertRaises(ValueError):
                index.download_package("example-1.0.0.tgz", str(repo_dir), "sha256:wrong", cache_dir=cache_dir)

    def test_download_package_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / "cache"
            cache_dir.mkdir()

            with self.assertRaises(FileNotFoundError):
                index.download_package("missing.tgz", tmp, "sha256:abc", cache_dir=cache_dir)
