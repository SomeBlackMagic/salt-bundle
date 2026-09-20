import unittest

from salt_bundle.dependencies.lock_models import LockFile
from salt_bundle.dependencies.lockfile import add_locked_dependency, remove_locked_dependency


class TestLockfile(unittest.TestCase):
    def test_lock_mutations(self) -> None:
        lock = LockFile()
        add_locked_dependency(lock, "example", "1.0.0", "source", "example.tgz", "sha256:abc")
        self.assertIn("example", lock.dependencies)
        remove_locked_dependency(lock, "example")
        self.assertEqual(lock.dependencies, {})
