"""YAML utilities for loading and dumping configuration files."""

from pathlib import Path
from typing import Any
import yaml


def load_yaml(file_path: Path | str) -> dict[str, Any]:
    """Load YAML file and return parsed content.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML content as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def dump_yaml(data: dict[str, Any], file_path: Path | str) -> None:
    """Dump data to YAML file.

    Args:
        data: Data to serialize
        file_path: Path to output YAML file

    Raises:
        yaml.YAMLError: If YAML serialization fails
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

