import os
import tempfile
import unittest
from unittest.mock import patch

from salt_bundle.config import add_user_repository, load_user_config


class TestUserConfig(unittest.TestCase):
    def test_user_config_add_and_load_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": temporary_directory}, clear=False):
                add_user_repository("main", "https://example.test/index")
                self.assertEqual(load_user_config().repositories[0].name, "main")
                with self.assertRaises(ValueError):
                    add_user_repository("main", "https://duplicate.test/index")
