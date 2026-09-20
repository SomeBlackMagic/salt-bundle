import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from salt_bundle.config.user_config import get_cache_dir, get_config_dir, load_user_config, save_user_config
from salt_bundle.config.models import UserConfig


class TestConfigExtended(unittest.TestCase):
    def test_get_config_dir_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=False):
                with patch("salt_bundle.config.user_config.Path.home", return_value=Path(tmp)):
                    config_dir = get_config_dir()
                    self.assertTrue(config_dir.exists())
                    self.assertIn("salt-bundle", str(config_dir))

    def test_get_cache_dir_with_xdg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CACHE_HOME": tmp}, clear=False):
                cache_dir = get_cache_dir()
                self.assertTrue(cache_dir.exists())
                self.assertEqual(cache_dir, Path(tmp) / "salt-bundle")

    def test_get_cache_dir_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CACHE_HOME": ""}, clear=False):
                with patch("salt_bundle.config.user_config.Path.home", return_value=Path(tmp)):
                    cache_dir = get_cache_dir()
                    self.assertTrue(cache_dir.exists())

    def test_load_user_config_returns_empty_if_no_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp}, clear=False):
                config = load_user_config()
                self.assertEqual(config.repositories, [])

    def test_save_and_load_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp}, clear=False):
                config = UserConfig()
                save_user_config(config)
                loaded = load_user_config()
                self.assertEqual(loaded.repositories, [])
