"""Errors raised by the target-aware activation layer."""


class ActivationError(Exception):
    """Base error for activation layer."""


class BundleTopSyntaxError(ActivationError):
    """Invalid ``top_bundle.sls`` syntax or structure."""

