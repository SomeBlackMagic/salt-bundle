"""Salt loader plugin for automatic formula loading from .salt-dependencies.yaml."""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List

log = logging.getLogger(__name__)


def _find_project_config() -> Path | None:
    """Find .salt-dependencies.yaml in current or parent directories.

    Returns:
        Path to .salt-dependencies.yaml or None
    """
    current = Path.cwd()

    # Check current directory and parents
    for parent in [current] + list(current.parents):
        config_file = parent / '.salt-dependencies.yaml'
        if config_file.exists():
            log.debug(f"Found project config at {config_file}")
            return config_file

    return None


def _load_project_config(config_path: Path) -> Dict[str, Any] | None:
    """Load project configuration.

    Args:
        config_path: Path to .salt-dependencies.yaml

    Returns:
        Configuration dictionary or None
    """
    try:
        from salt_bundle.utils.yaml import load_yaml
        from salt_bundle.models.config_models import ProjectConfig

        data = load_yaml(config_path)
        config = ProjectConfig(**data)
        return config.model_dump()
    except Exception as e:
        log.warning(f"Failed to load project config from {config_path}: {e}")
        return None


def _get_vendor_paths(project_dir: Path, vendor_dir: str) -> List[Path]:
    """Get list of formula paths in vendor directory.

    Args:
        project_dir: Project root directory
        vendor_dir: Vendor directory name

    Returns:
        List of formula paths
    """
    vendor_path = project_dir / vendor_dir
    if not vendor_path.exists():
        return []

    paths = []
    # Find all subdirectories in vendor (each = formula)
    for item in vendor_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            paths.append(item)
            log.debug(f"Found formula at {item}")

    return paths


def file_roots(opts: Dict[str, Any]) -> List[str]:
    """Salt loader for automatic vendor formula addition to file_roots.

    This loader is automatically invoked by Salt at startup.
    Searches for .salt-dependencies.yaml in CWD and adds vendor_dir to file_roots.

    Args:
        opts: Salt options

    Returns:
        List of formula paths
    """
    # Find project config
    config_path = _find_project_config()
    if not config_path:
        log.debug("No .salt-dependencies.yaml found in current directory tree")
        return []

    # Load config
    config = _load_project_config(config_path)
    if not config:
        return []

    project_dir = config_path.parent
    vendor_dir = config.get('vendor_dir', 'vendor')

    # Get formula paths
    formula_paths = _get_vendor_paths(project_dir, vendor_dir)

    if formula_paths:
        log.info(f"SaltBundle: Added {len(formula_paths)} formulas from {project_dir / vendor_dir}")

    return [str(path) for path in formula_paths]


def ext_pillar(minion_id: str, pillar: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """External pillar for adding saltbundle information to pillar.

    Args:
        minion_id: Minion ID
        pillar: Current pillar
        **kwargs: Additional parameters

    Returns:
        Dictionary to add to pillar
    """
    config_path = _find_project_config()
    if not config_path:
        return {}

    config = _load_project_config(config_path)
    if not config:
        return {}

    project_dir = config_path.parent
    vendor_dir = config.get('vendor_dir', 'vendor')
    formula_paths = _get_vendor_paths(project_dir, vendor_dir)

    return {
        'saltbundle': {
            'project_dir': str(project_dir),
            'vendor_dir': vendor_dir,
            'formulas': [path.name for path in formula_paths],
            'formula_paths': [str(path) for path in formula_paths]
        }
    }
