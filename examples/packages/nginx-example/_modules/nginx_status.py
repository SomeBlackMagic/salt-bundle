"""Custom execution module for Nginx status checks."""

import subprocess


def is_running():
    """Check if Nginx process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-x", "nginx"],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def version():
    """Return the installed Nginx version."""
    try:
        result = subprocess.run(
            ["nginx", "-v"],
            capture_output=True,
            text=True,
        )
        return result.stderr.strip()
    except FileNotFoundError:
        return "nginx not installed"
