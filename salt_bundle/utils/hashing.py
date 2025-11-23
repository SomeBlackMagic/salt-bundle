"""Hashing utilities for file integrity verification."""

import hashlib
from pathlib import Path


def calculate_sha256(file_path: Path | str) -> str:
    """Calculate SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hash in format "sha256:<hex>"

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    sha256_hash = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)

    return f"sha256:{sha256_hash.hexdigest()}"


def verify_digest(file_path: Path | str, expected_digest: str) -> bool:
    """Verify file digest matches expected value.

    Args:
        file_path: Path to file
        expected_digest: Expected digest in format "sha256:<hex>"

    Returns:
        True if digest matches, False otherwise

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If digest format is invalid
    """
    if not expected_digest.startswith("sha256:"):
        raise ValueError(f"Invalid digest format: {expected_digest}")

    actual_digest = calculate_sha256(file_path)
    return actual_digest == expected_digest
