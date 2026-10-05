"""Debian packaging scripts for salt-bundle."""

from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent


def get_script(name: str) -> Path:
    """Return path to a deb packaging script."""
    path = SCRIPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Packaging script not found: {name}")
    return path
