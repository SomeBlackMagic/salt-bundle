from pathlib import Path
import tempfile
import unittest

from salt_bundle.packaging.types import detect_package_type, load_package_meta


class TestPackageType(unittest.TestCase):
    def test_detects_extension_and_loads_extension_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_dir = Path(temporary_directory)
            (package_dir / "EXTENSION").write_text(
                "name: example-extension\nversion: 1.2.3\n",
                encoding="utf-8",
            )

            self.assertEqual(detect_package_type(package_dir), "extension")
            self.assertEqual(load_package_meta(package_dir).name, "example-extension")

    def test_rejects_package_directory_with_both_metadata_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_dir = Path(temporary_directory)
            (package_dir / "FORMULA").write_text("name: formula\nversion: 1.0.0\n", encoding="utf-8")
            (package_dir / "EXTENSION").write_text("name: extension\nversion: 1.0.0\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "both FORMULA and EXTENSION"):
                detect_package_type(package_dir)
