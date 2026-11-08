"""State module used by integration checks."""


def present(name):
    """Return a successful no-op state."""
    return {
        "name": name,
        "changes": {},
        "result": True,
        "comment": "extension state loaded",
    }
