"""Acceptance tests for target-aware runtime CLI commands."""

import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from salt_bundle.cli import cli


class TestRuntimeCommands(unittest.TestCase):
    """Verify the documented runtime command interface."""

    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        (self.project_dir / "Saltfile").write_text(
            "vendor_dir: vendor\n",
            encoding="utf-8",
        )
        (self.project_dir / "Saltfile.lock").write_text(
            """dependencies:
  community/linux-base:
    version: 3.1.4
    repository: default
    url: linux-base.tgz
    digest: sha256:linux-base
    dependencies: {}
  acme/nginx:
    version: 1.2.0
    repository: default
    url: nginx.tgz
    digest: sha256:nginx
    dependencies:
      community/systemd-helper: 1.0.0
  community/systemd-helper:
    version: 1.0.0
    repository: default
    url: systemd-helper.tgz
    digest: sha256:systemd-helper
    dependencies: {}
""",
            encoding="utf-8",
        )
        (self.project_dir / "top_bundle.sls").write_text(
            """base:
  '*':
    - community/linux-base
  'web-*':
    - acme/nginx
""",
            encoding="utf-8",
        )
        for package_name in (
            "community/linux-base",
            "acme/nginx",
            "community/systemd-helper",
        ):
            (self.project_dir / "vendor" / package_name).mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            cli,
            ["--project-dir", str(self.project_dir), *arguments],
        )

    def test_runtime_resolve_displays_target_environment_fingerprint_and_packages(self) -> None:
        result = self.invoke("runtime", "resolve", "web-01")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Target: web-01", result.output)
        self.assertIn("Environment: base", result.output)
        self.assertIn("Fingerprint: sha256:", result.output)
        self.assertIn("community/linux-base 3.1.4", result.output)
        self.assertIn("acme/nginx 1.2.0", result.output)
        self.assertIn("community/systemd-helper 1.0.0", result.output)

    def test_runtime_explain_displays_matching_rules_transitive_packages_and_final_set(self) -> None:
        result = self.invoke("runtime", "explain", "web-01")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Matched:", result.output)
        self.assertIn("'*'", result.output)
        self.assertIn("'web-*'", result.output)
        self.assertIn("Transitive:", result.output)
        self.assertIn("community/systemd-helper", result.output)
        self.assertIn("Final:", result.output)

    def test_runtime_validate_reports_unmaterialized_locked_package_as_error(self) -> None:
        (self.project_dir / "vendor" / "acme" / "nginx").rmdir()

        result = self.invoke("runtime", "validate")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("acme/nginx", result.output)
        self.assertIn("not found", result.output)

    def test_runtime_matrix_displays_each_target_with_its_fingerprint_and_packages(self) -> None:
        result = self.invoke("runtime", "matrix", "web-01", "db-01")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("TARGET", result.output)
        self.assertIn("FINGERPRINT", result.output)
        self.assertIn("PACKAGES", result.output)
        self.assertIn("web-01", result.output)
        self.assertIn("db-01", result.output)
        self.assertIn("acme/nginx", result.output)

    def test_exec_help_lists_the_required_runtime_backends(self) -> None:
        result = self.invoke("exec", "--help")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--backend", result.output)
        self.assertIn("ssh", result.output)
        self.assertIn("minion", result.output)

    def test_ssh_shortcut_is_registered(self) -> None:
        result = self.invoke("ssh", "--help")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("state.highstate", result.output)
