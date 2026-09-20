import tarfile
import tempfile
import unittest
from pathlib import Path

from salt_bundle.packaging.archives import pack_extension, unpack_package
from salt_bundle.dependencies.index import generate_index


class TestExtensionPackaging(unittest.TestCase):
    def test_pack_and_unpack_extension_with_salt_module_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            extension_dir = temporary_path / "example-extension"
            modules_dir = extension_dir / "_modules"
            modules_dir.mkdir(parents=True)
            (extension_dir / "EXTENSION").write_text(
                "name: example-extension\nversion: 1.2.3\n",
                encoding="utf-8",
            )
            (modules_dir / "example.py").write_text("def ping():\n    return True\n", encoding="utf-8")

            archive_path = pack_extension(extension_dir)

            with tarfile.open(archive_path, "r:gz") as archive:
                self.assertEqual(archive.getnames(), ["_modules/example.py", "EXTENSION"])

            installed_dir = temporary_path / "installed"
            unpack_package(archive_path, installed_dir)

            self.assertTrue((installed_dir / "EXTENSION").exists())
            self.assertTrue((installed_dir / "_modules" / "example.py").exists())

    def test_generates_extension_index_entry_with_extension_type(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_dir = Path(temporary_directory)
            (package_dir / "EXTENSION").write_text(
                "name: example-extension\nversion: 1.2.3\n",
                encoding="utf-8",
            )
            (package_dir / "_modules").mkdir()
            (package_dir / "_modules" / "example.py").write_text("", encoding="utf-8")
            pack_extension(package_dir, package_dir)

            index = generate_index(package_dir)

            self.assertEqual(index.packages["example-extension"][0].type, "extension")
