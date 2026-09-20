import unittest

from click.testing import CliRunner

from salt_bundle.cli import cli


class TestCliGroup(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_cli_main_group_shows_help(self) -> None:
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("package", result.output)
        self.assertIn("project", result.output)
        self.assertIn("repo", result.output)

    def test_package_subgroup_shows_help(self) -> None:
        result = self.runner.invoke(cli, ["package", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("init", result.output)
        self.assertIn("pack", result.output)
        self.assertIn("verify", result.output)
        self.assertIn("sync", result.output)

    def test_project_subgroup_shows_help(self) -> None:
        result = self.runner.invoke(cli, ["project", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("init", result.output)
        self.assertIn("install", result.output)
        self.assertIn("update", result.output)
        self.assertIn("vendor", result.output)

    def test_repo_subgroup_shows_help(self) -> None:
        result = self.runner.invoke(cli, ["repo", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("add", result.output)
        self.assertIn("index", result.output)
        self.assertIn("release", result.output)

    def test_cli_debug_flag(self) -> None:
        result = self.runner.invoke(cli, ["--debug", "package", "--help"])
        self.assertEqual(result.exit_code, 0)

    def test_cli_quiet_flag(self) -> None:
        result = self.runner.invoke(cli, ["--quiet", "package", "--help"])
        self.assertEqual(result.exit_code, 0)
