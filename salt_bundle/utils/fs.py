"""Filesystem utilities."""

import fnmatch
from pathlib import Path


DEFAULT_IGNORE_PATTERNS = [
    '.git',
    '.git/**',
    '__pycache__',
    '__pycache__/**',
    '*.pyc',
    '*.pyo',
    'tests',
    'tests/**',
    '.pytest_cache',
    '.pytest_cache/**',
    '*.egg-info',
    '*.egg-info/**',
]


def load_ignore_patterns(base_dir: Path) -> list[str]:
    """Load ignore patterns from .saltbundleignore file if exists.

    Args:
        base_dir: Base directory to look for .saltbundleignore

    Returns:
        List of ignore patterns (always includes defaults)
    """
    patterns = DEFAULT_IGNORE_PATTERNS.copy()
    ignore_file = base_dir / '.saltbundleignore'

    if ignore_file.exists():
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)

    return patterns


def should_ignore(path: Path, base_dir: Path, patterns: list[str]) -> bool:
    """Check if path should be ignored based on patterns.

    Args:
        path: Path to check
        base_dir: Base directory for relative path calculation
        patterns: List of glob patterns

    Returns:
        True if path should be ignored
    """
    try:
        rel_path = path.relative_to(base_dir)
    except ValueError:
        return False

    rel_path_str = str(rel_path)

    for pattern in patterns:
        # Check full relative path
        if fnmatch.fnmatch(rel_path_str, pattern):
            return True

        # Check just the filename
        if fnmatch.fnmatch(path.name, pattern):
            return True

        # Check each parent directory in the path
        # This handles cases like .github, .idea directories
        for part in rel_path.parts:
            if fnmatch.fnmatch(part, pattern):
                return True
            # Also check if pattern matches the directory exactly
            if part == pattern.rstrip('/'):
                return True

    return False


def collect_files(base_dir: Path, patterns: list[str] | None = None) -> list[Path]:
    """Collect all files in directory respecting ignore patterns.

    Args:
        base_dir: Base directory to scan
        patterns: Ignore patterns (if None, loads from .saltbundleignore)

    Returns:
        List of file paths to include in package
    """
    if patterns is None:
        patterns = load_ignore_patterns(base_dir)

    files = []
    for path in base_dir.rglob('*'):
        if path.is_file() and not should_ignore(path, base_dir, patterns):
            files.append(path)

    return files
