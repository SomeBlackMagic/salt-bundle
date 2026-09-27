"""Tests for activation-time package security checks."""

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from salt_bundle.activation import errors, resolver


class TestPackagePathValidation(unittest.TestCase):
    """Specify that activation cannot escape the materialized package store."""

    def test_accepts_a_package_directory_inside_the_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            allowed_root = Path(directory) / "vendor"
            package_path = allowed_root / "acme" / "nginx"
            package_path.mkdir(parents=True)

            resolver.validate_package_path(package_path, allowed_root)

    def test_rejects_a_path_that_escapes_the_allowed_root_with_parent_segments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            allowed_root = root / "vendor"
            allowed_root.mkdir()
            escaped_path = allowed_root / ".." / "outside-package"

            with self.assertRaises(errors.SecurityError):
                resolver.validate_package_path(escaped_path, allowed_root)

    def test_rejects_a_symlinked_package_directory_that_escapes_the_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            allowed_root = root / "vendor"
            allowed_root.mkdir()
            outside_package = root / "outside-package"
            outside_package.mkdir()
            escaped_path = allowed_root / "acme-nginx"
            escaped_path.symlink_to(outside_package, target_is_directory=True)

            with self.assertRaises(errors.SecurityError):
                resolver.validate_package_path(escaped_path, allowed_root)


class TestPackageDigestVerification(unittest.TestCase):
    """Specify integrity checks for materialized package contents."""

    @staticmethod
    def _package_digest(package_path: Path) -> str:
        digest = sha256()
        for child_path in sorted(package_path.rglob("*")):
            if child_path.is_file():
                relative_path = child_path.relative_to(package_path).as_posix()
                digest.update(relative_path.encode("utf-8"))
                digest.update(b"\0")
                digest.update(child_path.read_bytes())
                digest.update(b"\0")
        return f"sha256:{digest.hexdigest()}"

    def test_accepts_a_package_whose_canonical_content_digest_matches_the_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package_path = Path(directory) / "acme" / "nginx"
            module_path = package_path / "_modules" / "nginx.py"
            module_path.parent.mkdir(parents=True)
            module_path.write_text("def version():\n    return '1.2.0'\n", encoding="utf-8")

            resolver.verify_package_digest(package_path, self._package_digest(package_path))

    def test_rejects_a_package_whose_contents_changed_after_locking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package_path = Path(directory) / "acme" / "nginx"
            module_path = package_path / "_modules" / "nginx.py"
            module_path.parent.mkdir(parents=True)
            module_path.write_text("def version():\n    return '1.2.0'\n", encoding="utf-8")
            expected_digest = self._package_digest(package_path)
            module_path.write_text("def version():\n    return 'tampered'\n", encoding="utf-8")

            with self.assertRaises(errors.SecurityError):
                resolver.verify_package_digest(package_path, expected_digest)
