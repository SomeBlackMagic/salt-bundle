"""CLI coverage for legacy projects without ``top_bundle.sls``."""

import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from salt_bundle.cli import cli


class TestRuntimeBackwardCompatibility(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        (self.project_dir / "Saltfile").write_text("vendor_dir: vendor\n", encoding="utf-8")
        (self.project_dir / "Saltfile.lock").write_text(
            """dependencies:
  acme/nginx:
    version: 1.2.0
    repository: default
    url: nginx.tar.gz
    digest: sha256:nginx
    type: formula
""",
            encoding="utf-8",
        )
        (self.project_dir / "vendor" / "acme" / "nginx").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_runtime_resolve_without_top_bundle_uses_legacy_global_activation(self) -> None:
        result = self.runner.invoke(
            cli,
            ["--project-dir", str(self.project_dir), "runtime", "resolve", "web-01"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("acme/nginx 1.2.0", result.output)

    def test_runtime_resolve_without_top_bundle_fails_when_strict_mode_is_enabled(self) -> None:
        (self.project_dir / "Saltfile").write_text(
            "runtime:\n  require_bundle_top: true\n",
            encoding="utf-8",
        )

        result = self.runner.invoke(
            cli,
            ["--project-dir", str(self.project_dir), "runtime", "resolve", "web-01"],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("top_bundle.sls is required", result.output)
