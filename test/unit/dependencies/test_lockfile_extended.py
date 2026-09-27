import tempfile
import unittest
from pathlib import Path

from salt_bundle.dependencies.lockfile import load_lockfile, save_lockfile, lockfile_exists, add_locked_dependency
from salt_bundle.dependencies.lock_models import LockFile


class TestLockfileExtended(unittest.TestCase):
    def test_save_and_load_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            lock = LockFile()
            add_locked_dependency(lock, "example", "1.0.0", "source", "example.tgz", "sha256:abc")
            save_lockfile(lock, project_dir)

            self.assertTrue(lockfile_exists(project_dir))
            loaded = load_lockfile(project_dir)
            self.assertIn("example", loaded.dependencies)
            self.assertEqual(loaded.dependencies["example"].version, "1.0.0")

    def test_lockfile_exists_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(lockfile_exists(tmp))

    def test_load_lockfile_nonexistent_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = load_lockfile(tmp)
            self.assertEqual(lock.dependencies, {})

    def test_load_lockfile_parses_transitive_dependency_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "Saltfile.lock").write_text(
                """dependencies:
  acme/nginx:
    version: 1.2.0
    repository: default
    url: https://packages.example.test/acme-nginx.tar.gz
    digest: sha256:abc
    type: formula
    dependencies:
      community/linux-base: 3.1.4
""",
                encoding="utf-8",
            )

            lockfile = load_lockfile(project_dir)

        self.assertEqual(
            lockfile.dependencies["acme/nginx"].dependencies,
            {"community/linux-base": "3.1.4"},
        )

    def test_load_lockfile_without_dependency_graph_remains_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "Saltfile.lock").write_text(
                """dependencies:
  acme/nginx:
    version: 1.2.0
    repository: default
    url: https://packages.example.test/acme-nginx.tar.gz
    digest: sha256:abc
    type: formula
""",
                encoding="utf-8",
            )

            lockfile = load_lockfile(project_dir)

        self.assertEqual(lockfile.dependencies["acme/nginx"].dependencies, {})
