"""
Functional test fixtures for salt-bundle ↔ Salt integration.

These tests require a working Salt installation (salt-call, salt-run).
Run inside the Docker dev container or on a host where Salt + salt-bundle
are installed into the same Python environment.
"""

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Generator

import pytest
import yaml


# ---------------------------------------------------------------------------
# Project root detection
# ---------------------------------------------------------------------------

def _find_project_root() -> Path:
    """Find the salt-pkg project root (works both locally and inside Kitchen)."""
    # Kitchen container: project is at /tmp/salt-pkg
    kitchen_root = Path("/tmp/salt-pkg")
    if kitchen_root.is_dir() and (kitchen_root / "examples").is_dir():
        return kitchen_root

    # Local: walk up from this file
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _find_project_root()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def salt_call(*args: str, cwd: str | Path | None = None, timeout: int = 30) -> dict:
    """Run ``salt-call --local`` and return parsed JSON output.

    Returns a dict with keys:
        returncode, stdout, stderr, json (parsed --out=json when possible)
    """
    cmd = ["salt-call", "--local", "--out=json", "--log-level=warning", *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    parsed = None
    if result.returncode == 0 and result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "json": parsed,
    }


def salt_call_raw(*args: str, cwd: str | Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run ``salt-call --local`` without JSON parsing (for custom outputters etc.)."""
    cmd = ["salt-call", "--local", "--log-level=warning", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


# ---------------------------------------------------------------------------
# Skip marker – tests require a real Salt installation
# ---------------------------------------------------------------------------

def _salt_available() -> bool:
    try:
        r = subprocess.run(
            ["salt-call", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


requires_salt = pytest.mark.skipif(
    not _salt_available(),
    reason="salt-call not found – functional tests require Salt",
)

pytestmark = requires_salt


# ---------------------------------------------------------------------------
# Fixture: formula package in vendor
# ---------------------------------------------------------------------------

@pytest.fixture()
def project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a minimal salt-bundle project with a single formula in vendor.

    Layout::

        tmp/
        ├── Saltfile
        └── vendor/
            └── foo/
                ├── .saltbundle.yaml
                ├── _modules/test_module.py
                ├── _states/test_state.py
                ├── _grains/test_grain.py
                ├── _renderers/test_renderer.py
                ├── _returners/test_returner.py
                ├── _beacons/test_beacon.py
                ├── _utils/test_utils.py
                ├── _serializers/test_serializer.py
                ├── _executors/test_executor.py
                ├── _output/test_output.py
                ├── _runners/test_runner.py
                ├── init.sls
                └── defaults.sls
    """
    # Copy foo example package to vendor
    examples_dir = PROJECT_ROOT / "examples" / "packages" / "foo"
    vendor = tmp_path / "vendor" / "foo"
    shutil.copytree(examples_dir, vendor)

    # Write Saltfile
    saltfile = tmp_path / "Saltfile"
    saltfile.write_text(yaml.dump({"vendor_dir": "vendor"}))

    yield tmp_path


@pytest.fixture()
def multi_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Project with two formula packages in vendor (foo + bar)."""
    examples = PROJECT_ROOT / "examples" / "packages"

    for pkg_name in ("foo", "bar"):
        src = examples / pkg_name
        dst = tmp_path / "vendor" / pkg_name
        shutil.copytree(src, dst)

    saltfile = tmp_path / "Saltfile"
    saltfile.write_text(yaml.dump({"vendor_dir": "vendor"}))

    yield tmp_path


@pytest.fixture()
def extension_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Project with a saltext-style extension package.

    Layout::

        tmp/
        ├── Saltfile
        └── vendor/
            └── myext/
                ├── EXTENSION
                └── src/saltext/myext/
                    ├── modules/my_ext_mod.py
                    └── states/my_ext_state.py
    """
    ext_root = tmp_path / "vendor" / "myext"
    saltext = ext_root / "src" / "saltext" / "myext"

    (saltext / "modules").mkdir(parents=True)
    (saltext / "states").mkdir(parents=True)

    (ext_root / "EXTENSION").write_text(yaml.dump({
        "name": "myext",
        "version": "0.1.0",
        "description": "Test extension",
    }))

    (saltext / "modules" / "my_ext_mod.py").write_text(textwrap.dedent("""\
        def ping():
            return "extension module loaded"
    """))

    (saltext / "states" / "my_ext_state.py").write_text(textwrap.dedent("""\
        def present(name):
            return {
                "name": name,
                "result": True,
                "changes": {},
                "comment": "extension state loaded",
            }
    """))

    saltfile = tmp_path / "Saltfile"
    saltfile.write_text(yaml.dump({"vendor_dir": "vendor"}))

    yield tmp_path


@pytest.fixture()
def mixed_project_dir(
    tmp_path: Path,
) -> Generator[Path, None, None]:
    """Project with both a formula (foo) and a saltext extension."""
    # Formula
    examples_dir = PROJECT_ROOT / "examples" / "packages" / "foo"
    shutil.copytree(examples_dir, tmp_path / "vendor" / "foo")

    # Extension
    ext_root = tmp_path / "vendor" / "myext"
    saltext = ext_root / "src" / "saltext" / "myext"
    (saltext / "modules").mkdir(parents=True)
    (ext_root / "EXTENSION").write_text(yaml.dump({
        "name": "myext",
        "version": "0.1.0",
        "description": "Test extension",
    }))
    (saltext / "modules" / "my_ext_mod.py").write_text(textwrap.dedent("""\
        def ping():
            return "extension module loaded"
    """))

    saltfile = tmp_path / "Saltfile"
    saltfile.write_text(yaml.dump({"vendor_dir": "vendor"}))

    yield tmp_path


@pytest.fixture()
def two_level_vendor_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Project with two-level vendor tree: vendor/{vendor_name}/{package_name}.

    Layout::

        vendor/
        └── acme/
            └── web/
                ├── .saltbundle.yaml
                ├── _modules/acme_web.py
                └── _states/acme_web.py
    """
    pkg = tmp_path / "vendor" / "acme" / "web"
    (pkg / "_modules").mkdir(parents=True)
    (pkg / "_states").mkdir(parents=True)

    (pkg / ".saltbundle.yaml").write_text(yaml.dump({
        "name": "acme-web",
        "version": "1.0.0",
        "description": "Acme web formula",
    }))

    (pkg / "_modules" / "acme_web.py").write_text(textwrap.dedent("""\
        def ping():
            return "acme-web module loaded"
    """))

    (pkg / "_states" / "acme_web.py").write_text(textwrap.dedent("""\
        def present(name):
            return {
                "name": name,
                "result": True,
                "changes": {},
                "comment": "acme-web state loaded",
            }
    """))

    (pkg / "init.sls").write_text("# acme-web init\n")

    saltfile = tmp_path / "Saltfile"
    saltfile.write_text(yaml.dump({"vendor_dir": "vendor"}))

    yield tmp_path
