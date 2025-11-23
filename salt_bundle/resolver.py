"""Dependency resolution using semantic versioning."""

from typing import Iterable, Optional

import semver

from .models.index_models import IndexEntry


def parse_version(version_str: str) -> semver.Version:
    """Parse version string to semver.Version object.

    Args:
        version_str: Version string

    Returns:
        semver.Version object

    Raises:
        ValueError: If version string is invalid
    """
    try:
        return semver.Version.parse(version_str)
    except ValueError as e:
        raise ValueError(f"Invalid version: {version_str}") from e


def matches_constraint(version: str, constraint: str) -> bool:
    """Check if version matches constraint.

    Supports:
    - Exact: "1.2.3"
    - Caret: "^1.2.3" (compatible with 1.x.x, but not 2.x.x)
    - Tilde: "~1.2.3" (compatible with 1.2.x)
    - Range: ">=1.0.0,<2.0.0"
    - Wildcard: "1.2.x" or "1.2.*"

    Args:
        version: Version string to check
        constraint: Constraint string

    Returns:
        True if version matches constraint
    """
    try:
        ver = parse_version(version)
    except ValueError:
        return False

    constraint = constraint.strip()

    # Exact match
    if not any(c in constraint for c in ['^', '~', '>', '<', '=', '*', 'x', ',']):
        try:
            constraint_ver = parse_version(constraint)
            return ver == constraint_ver
        except ValueError:
            return False

    # Caret (^)
    if constraint.startswith('^'):
        try:
            base = parse_version(constraint[1:])
            # Compatible with same major version (if major > 0)
            # or same minor version (if major == 0)
            if base.major > 0:
                return ver.major == base.major and ver >= base
            elif base.minor > 0:
                return ver.major == 0 and ver.minor == base.minor and ver >= base
            else:
                return ver.major == 0 and ver.minor == 0 and ver.patch == base.patch
        except ValueError:
            return False

    # Tilde (~)
    if constraint.startswith('~'):
        try:
            base = parse_version(constraint[1:])
            # Compatible with same major.minor version
            return ver.major == base.major and ver.minor == base.minor and ver >= base
        except ValueError:
            return False

    # Wildcard (x or *)
    if 'x' in constraint or '*' in constraint:
        parts = constraint.replace('*', 'x').split('.')
        ver_parts = [ver.major, ver.minor, ver.patch]
        
        for i, part in enumerate(parts):
            if part == 'x':
                continue
            try:
                if i < len(ver_parts) and int(part) != ver_parts[i]:
                    return False
            except ValueError:
                return False
        return True

    # Range (>=, <=, >, <, =)
    if ',' in constraint:
        # Multiple conditions
        conditions = [c.strip() for c in constraint.split(',')]
        return all(matches_constraint(version, cond) for cond in conditions)

    # Single comparison operator
    for op in ['>=', '<=', '>', '<', '=']:
        if constraint.startswith(op):
            try:
                constraint_ver = parse_version(constraint[len(op):].strip())
                if op == '>=':
                    return ver >= constraint_ver
                elif op == '<=':
                    return ver <= constraint_ver
                elif op == '>':
                    return ver > constraint_ver
                elif op == '<':
                    return ver < constraint_ver
                elif op == '=':
                    return ver == constraint_ver
            except ValueError:
                return False

    return False


def resolve_version(
    constraint: str,
    candidates: Iterable[IndexEntry],
) -> Optional[IndexEntry]:
    """Resolve version constraint to best matching candidate.

    Args:
        constraint: Version constraint (semver range)
        candidates: Available versions

    Returns:
        Best matching IndexEntry or None if no match
    """
    matching = []
    
    for entry in candidates:
        if matches_constraint(entry.version, constraint):
            matching.append(entry)

    if not matching:
        return None

    # Sort by version (descending) and return latest
    try:
        matching.sort(key=lambda e: parse_version(e.version), reverse=True)
        return matching[0]
    except ValueError:
        # Fallback to string comparison if parsing fails
        matching.sort(key=lambda e: e.version, reverse=True)
        return matching[0]
