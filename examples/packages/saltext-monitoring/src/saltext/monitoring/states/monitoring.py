"""State module for monitoring health assertions.

Usage in SLS:
    check_disk:
      monitoring.disk_below:
        - path: /
        - max_percent: 90

    check_memory:
      monitoring.memory_below:
        - max_percent: 85
"""


def disk_below(name, path="/", max_percent=90):
    """Assert disk usage is below a threshold."""
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    usage = __salt__["monitoring.disk_usage"](path)
    if "error" in usage:
        ret["result"] = False
        ret["comment"] = usage["error"]
        return ret

    if usage["percent"] > max_percent:
        ret["result"] = False
        ret["comment"] = (
            f"Disk usage on {path} is {usage['percent']}%, "
            f"exceeds threshold of {max_percent}%"
        )
    else:
        ret["comment"] = (
            f"Disk usage on {path} is {usage['percent']}%, "
            f"within threshold of {max_percent}%"
        )
    return ret


def memory_below(name, max_percent=85):
    """Assert memory usage is below a threshold."""
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}

    mem = __salt__["monitoring.memory"]()
    if "error" in mem:
        ret["result"] = False
        ret["comment"] = mem["error"]
        return ret

    if mem["percent"] > max_percent:
        ret["result"] = False
        ret["comment"] = (
            f"Memory usage is {mem['percent']}%, "
            f"exceeds threshold of {max_percent}%"
        )
    else:
        ret["comment"] = (
            f"Memory usage is {mem['percent']}%, "
            f"within threshold of {max_percent}%"
        )
    return ret
