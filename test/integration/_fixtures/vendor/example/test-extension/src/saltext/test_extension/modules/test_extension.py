"""Execution module used by integration checks."""


def ping():
    """Return a stable marker for loader checks."""
    return "extension loaded"


def use_utils():
    return __utils__["extension_utils.hello"]()
