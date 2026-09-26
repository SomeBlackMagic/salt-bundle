"""Errors raised by the target-aware activation layer."""


class ActivationError(Exception):
    """Base error for activation layer."""


class BundleTopSyntaxError(ActivationError):
    """Invalid ``top_bundle.sls`` syntax or structure."""


class UnknownPackageError(ActivationError):
    """A package referenced by the activation map is absent from the lock file."""

    def __init__(self, package_name: str, saltenv: str = "base") -> None:
        super().__init__(
            f"Unknown package '{package_name}' in environment '{saltenv}'"
        )


class PackageNotMaterializedError(ActivationError):
    """A locked package is not available in the local vendor directory."""

    def __init__(self, package_name: str, expected_path: str) -> None:
        super().__init__(
            f"Package '{package_name}' not found at '{expected_path}'. "
            "Run 'salt-bundle project install' first."
        )


class RuntimeConflictError(ActivationError):
    """Active packages conflict in their runtime contents."""


class RuntimeManifestError(ActivationError):
    """A runtime manifest is malformed or uses an unsupported schema."""
