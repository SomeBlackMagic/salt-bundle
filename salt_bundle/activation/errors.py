"""Errors raised by the target-aware activation layer."""


class ActivationError(Exception):
    """Base error for activation layer."""


class BundleTopSyntaxError(ActivationError):
    """Invalid ``top_bundle.sls`` syntax or structure."""


class UnknownPackageError(ActivationError):
    """A package referenced by the activation map is absent from the lock file."""

    def __init__(self, package_name: str, saltenv: str = "base") -> None:
        self.package_name = package_name
        self.saltenv = saltenv
        super().__init__(
            f"Unknown package '{package_name}' in environment '{saltenv}'"
        )


class PackageNotMaterializedError(ActivationError):
    """A locked package is not available in the local vendor directory."""

    def __init__(self, package_name: str, expected_path: str) -> None:
        self.package_name = package_name
        self.expected_path = expected_path
        super().__init__(
            f"Package '{package_name}' not found at '{expected_path}'. "
            "Run 'salt-bundle project install' first."
        )


class RuntimeConflictError(ActivationError):
    """Active packages conflict in their runtime contents."""


class ExplicitConflictError(RuntimeConflictError):
    """Two active packages explicitly declare a conflict with one another."""

    def __init__(self, package_a: str, package_b: str) -> None:
        super().__init__(
            f"Packages '{package_a}' and '{package_b}' declare explicit conflict"
        )


class NamespaceCollisionError(RuntimeConflictError):
    """Multiple active packages provide one Salt loader namespace path."""

    def __init__(self, path: str, providers: list[str]) -> None:
        self.path = path
        self.providers = providers
        super().__init__(f"{path} is provided by: {', '.join(providers)}")


class RuntimeManifestError(ActivationError):
    """A runtime manifest is malformed or uses an unsupported schema."""
