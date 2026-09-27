"""Errors raised while a runtime backend is prepared or executed."""


class BackendPreparationError(Exception):
    """Failed to prepare a target-specific runtime for execution."""


class BackendExecutionError(Exception):
    """Failed to execute a Salt command through a prepared backend."""
