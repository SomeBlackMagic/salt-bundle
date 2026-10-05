"""Execution module for host monitoring.

Usage:
    salt '*' monitoring.health
    salt '*' monitoring.disk_usage /
    salt '*' monitoring.memory
"""

import shutil


def health():
    """Return a summary of host health metrics."""
    return {
        "disk": disk_usage("/"),
        "memory": memory(),
        "load": _load_average(),
    }


def disk_usage(path="/"):
    """Return disk usage for the given path."""
    usage = shutil.disk_usage(path)
    return {
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round(usage.used / (1024**3), 2),
        "free_gb": round(usage.free / (1024**3), 2),
        "percent": round(usage.used / usage.total * 100, 1),
    }


def memory():
    """Return memory usage from /proc/meminfo."""
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                key, value = line.split(":", 1)
                info[key.strip()] = int(value.strip().split()[0])
    except (FileNotFoundError, ValueError):
        return {"error": "cannot read /proc/meminfo"}

    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", 0)
    used = total - available

    return {
        "total_mb": round(total / 1024, 1),
        "used_mb": round(used / 1024, 1),
        "available_mb": round(available / 1024, 1),
        "percent": round(used / total * 100, 1) if total else 0,
    }


def _load_average():
    """Return system load averages."""
    try:
        with open("/proc/loadavg") as f:
            parts = f.read().split()
            return {
                "1min": float(parts[0]),
                "5min": float(parts[1]),
                "15min": float(parts[2]),
            }
    except (FileNotFoundError, ValueError, IndexError):
        return {"error": "cannot read /proc/loadavg"}
