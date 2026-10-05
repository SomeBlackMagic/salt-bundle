"""Tests for linked local package sources."""

import tempfile
import unittest
from pathlib import Path

from salt_bundle.dependencies.path_source import (
    calculate_dir_digest,
    install_from_path_link,
    install_from_path_snapshot,
)


class TestPathSourceLink(unittest.TestCase):
    def test_snapshot_with_top_level_dir_copies_entire_source_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_dir = root / "source"
            states_dir = source_dir / "states"
            modules_dir = source_dir / "_modules"
            states_dir.mkdir(parents=True)
            modules_dir.mkdir()
            (source_dir / "FORMULA").write_text(
                "name: acme/nginx\nversion: 1.0.0\ntop_level_dir: states\n",
                encoding="utf-8",
            )
            (source_dir / "README.md").write_text("formula documentation\n", encoding="utf-8")
            (source_dir / "FORMULAIGNORE").write_text("ignored.txt\n", encoding="utf-8")
            (source_dir / "ignored.txt").write_text("ignored\n", encoding="utf-8")
            (states_dir / "init.sls").write_text("nginx: []\n", encoding="utf-8")
            (modules_dir / "nginx.py").write_text("def present(): pass\n", encoding="utf-8")

            installed = install_from_path_snapshot(source_dir, "acme/nginx", root / "vendor")

            self.assertEqual(installed, root / "vendor" / "acme" / "nginx")
            self.assertTrue((installed / "FORMULA").is_file())
            self.assertTrue((installed / "README.md").is_file())
            self.assertTrue((installed / "FORMULAIGNORE").is_file())
            self.assertTrue((installed / "states" / "init.sls").is_file())
            self.assertTrue((installed / "_modules" / "nginx.py").is_file())
            self.assertFalse((installed / "ignored.txt").exists())
            self.assertEqual(calculate_dir_digest(source_dir), calculate_dir_digest(installed))

    def test_link_with_top_level_dir_links_the_entire_source_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_dir = root / "source"
            payload_dir = source_dir / "states"
            payload_dir.mkdir(parents=True)
            formula = source_dir / "FORMULA"
            init_state = payload_dir / "init.sls"
            formula.write_text(
                "name: acme/nginx\nversion: 1.0.0\ntop_level_dir: states\n",
                encoding="utf-8",
            )
            init_state.write_text("nginx: []\n", encoding="utf-8")

            installed = install_from_path_link(
                source_dir, "acme/nginx", root / "vendor"
            )

            self.assertTrue(installed.is_symlink())
            self.assertEqual(installed.resolve(), source_dir)
            self.assertEqual((installed / "FORMULA").resolve(), formula)
            self.assertEqual((installed / "states" / "init.sls").resolve(), init_state)
