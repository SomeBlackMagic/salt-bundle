"""Custom grains for Nginx installation info."""

import subprocess


def nginx_info():
    """Detect Nginx installation and return grain data."""
    grains = {}

    try:
        result = subprocess.run(
            ["nginx", "-v"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            grains["nginx"] = {
                "installed": True,
                "version": result.stderr.strip().split("/")[-1],
            }
        else:
            grains["nginx"] = {"installed": False}
    except FileNotFoundError:
        grains["nginx"] = {"installed": False}

    return grains
