import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from salt_bundle.salt import fileserver, loader, pillar


class TestSaltIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        self.package_dir = self.project_dir / "vendor" / "example"
        (self.package_dir / "_modules").mkdir(parents=True)
        (self.package_dir / "_states").mkdir()
        (self.package_dir / "init.sls").write_text("test: true\n", encoding="utf-8")
        (self.package_dir / "_modules" / "example.py").write_text("def ping(): return True\n", encoding="utf-8")
        (self.package_dir / "_states" / "example.py").write_text("def present(): return {}\n", encoding="utf-8")
        loader._CACHE.update(config_path=None, config_mtime=None, config_data=None, formulas=None)
        loader._get_module_dirs.cache_clear()
        fileserver._CACHE.update(config_path=None, vendor_roots=None)
        loader.__opts__ = {"config_dir": str(self.project_dir / "conf")}
        fileserver.__opts__ = {"config_dir": str(self.project_dir / "conf"), "file_buffer_size": 4}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_loader_exposes_all_configured_module_directories(self) -> None:
        expected_modules = str((self.package_dir / "_modules").absolute())
        expected_states = str((self.package_dir / "_states").absolute())

        self.assertEqual(loader.module_dirs(), [expected_modules])
        self.assertEqual(loader.states_dirs(), [expected_states])
        for function_name in (
            "auth_dirs", "cache_dirs", "executor_dirs", "grains_dirs", "log_handlers_dirs",
            "matchers_dirs", "metaproxy_dirs", "netapi_dirs", "pillar_dirs", "queue_dirs",
            "returner_dirs", "roster_dirs", "runner_dirs", "sdb_dirs", "serializers_dirs",
            "outputter_dirs", "pkgdb_dirs", "pkgfiles_dirs", "top_dirs", "utils_dirs",
            "wrapper_dirs", "render_dirs", "engines_dirs", "proxy_dirs", "cloud_dirs",
            "beacons_dirs", "thorium_dirs", "tokens_dirs", "wheel_dirs",
        ):
            self.assertEqual(getattr(loader, function_name)(), [])
        self.assertEqual(loader.configure({"id": "minion"}), {"id": "minion"})

    def test_fileserver_serves_package_and_special_module_files(self) -> None:
        self.assertEqual(fileserver.__virtual__(), "bundlefs")
        self.assertEqual(fileserver.envs(), ["base"])
        formula_file = fileserver.find_file("example/init.sls")
        module_file = fileserver.find_file("_modules/example.py")
        self.assertTrue(formula_file["path"].endswith("init.sls"))
        self.assertTrue(module_file["path"].endswith("_modules/example.py"))
        self.assertEqual(fileserver.find_file("missing"), {"path": "", "rel": ""})
        self.assertEqual(fileserver.find_file("unknown/init.sls"), {"path": "", "rel": ""})

        self.assertEqual(
            fileserver.file_list({}),
            ["_modules/example.py", "_states/example.py", "example/init.sls"],
        )
        self.assertIn("_modules", fileserver.dir_list({}))
        expected_hash = hashlib.sha256((self.package_dir / "init.sls").read_bytes()).hexdigest()
        self.assertEqual(fileserver.file_hash({}, formula_file)["hsum"], expected_hash)
        self.assertEqual(fileserver.file_hash({}, {}), {})
        self.assertEqual(fileserver.serve_file({"loc": 0}, formula_file)["data"], b"test")
        self.assertEqual(fileserver.serve_file({}, {})["data"], "")
        self.assertTrue(fileserver.update())

    def test_pillar_reports_project_packages(self) -> None:
        with patch.object(pillar, "__virtualname__", "saltbundle"):
            self.assertEqual(pillar.__virtual__(), "saltbundle")
        result = pillar.ext_pillar("minion", {})
        self.assertEqual(result["saltbundle"]["formulas"], ["example"])
        self.assertEqual(result["saltbundle"]["vendor_dir"], "vendor")
