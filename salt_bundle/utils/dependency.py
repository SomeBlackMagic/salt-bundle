"""Dependency name parsing utilities."""

from typing import Optional


def parse_dependency_name(dep_key: str) -> tuple[Optional[str], str]:
    """Parse dependency key in format 'repo/package' or just 'package'.

    Args:
        dep_key: Dependency key from .salt-dependencies.yaml
                 Examples: "main/nginx", "nginx", "local/my-formula"

    Returns:
        Tuple of (repo_name, package_name)
        - If format is "repo/package": ("repo", "package")
        - If format is "package": (None, "package")

    Examples:
        >>> parse_dependency_name("main/nginx")
        ("main", "nginx")

        >>> parse_dependency_name("nginx")
        (None, "nginx")

    Raises:
        ValueError: If format is invalid (e.g., "a/b/c")
    """
    if '/' not in dep_key:
        # Simple package name
        return (None, dep_key)

    parts = dep_key.split('/')
    if len(parts) != 2:
        raise ValueError(
            f"Invalid dependency format: '{dep_key}'. "
            f"Expected 'repo/package' or 'package'"
        )

    repo_name, pkg_name = parts

    if not repo_name or not pkg_name:
        raise ValueError(
            f"Invalid dependency format: '{dep_key}'. "
            f"Both repo and package names must be non-empty"
        )

    return (repo_name, pkg_name)


def format_dependency_key(repo_name: Optional[str], pkg_name: str) -> str:
    """Format dependency key from components.

    Args:
        repo_name: Repository name (can be None)
        pkg_name: Package name

    Returns:
        Formatted dependency key

    Examples:
        >>> format_dependency_key("main", "nginx")
        "main/nginx"

        >>> format_dependency_key(None, "nginx")
        "nginx"
    """
    if repo_name:
        return f"{repo_name}/{pkg_name}"
    return pkg_name
