"""Filesystem utilities."""

from pathlib import Path

import pathspec


DEFAULT_IGNORE_PATTERNS = [
    '.git/',
    '__pycache__/',
    '*.pyc',
    '*.pyo',
    'tests/',
    '.pytest_cache/',
    '*.egg-info/',
]


def load_ignore_patterns(base_dir: Path, ignore_filename: str = 'FORMULAIGNORE') -> pathspec.PathSpec:
    """Load ignore patterns from ignore file if it exists.

    Args:
        base_dir: Base directory to look for ignore file
        ignore_filename: Name of the ignore file (FORMULAIGNORE or EXTENSIONIGNORE)

    Returns:
        Compiled pathspec with gitignore semantics
    """
    lines = list(DEFAULT_IGNORE_PATTERNS)
    ignore_file = base_dir / ignore_filename

    if ignore_file.exists():
        with open(ignore_file, 'r', encoding='utf-8') as f:
            lines.extend(f.read().splitlines())

    return pathspec.PathSpec.from_lines('gitwildmatch', lines)


def should_ignore(path: Path, base_dir: Path, spec: pathspec.PathSpec) -> bool:
    """Check if path should be ignored.

    Args:
        path: Path to check
        base_dir: Base directory for relative path calculation
        spec: Compiled pathspec

    Returns:
        True if path should be ignored
    """
    try:
        rel_path = path.relative_to(base_dir)
    except ValueError:
        return False

    return spec.match_file(str(rel_path))


def collect_files(base_dir: Path, spec: pathspec.PathSpec | None = None) -> list[Path]:
    """Collect all files in directory respecting ignore patterns.

    Args:
        base_dir: Base directory to scan
        spec: Compiled pathspec (if None, loads from FORMULAIGNORE)

    Returns:
        List of file paths to include in package
    """
    if spec is None:
        spec = load_ignore_patterns(base_dir)

    files = []
    for path in base_dir.rglob('*'):
        if path.is_file() and not should_ignore(path, base_dir, spec):
            files.append(path)

    return files
