"""Execution module used by integration checks."""


def ping():
    """Return a stable marker for loader checks."""
    return "extension loaded"
