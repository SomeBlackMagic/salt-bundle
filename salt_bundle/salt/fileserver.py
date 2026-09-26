# -*- coding: utf-8 -*-
"""
bundlefs fileserver backend.

Automatically discovers and serves files from vendor formulas.
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from salt_bundle.package_layout import (
    detect_package_type,
    discover_package_paths,
    resolve_namespace_dir,
)

log = logging.getLogger(__name__)

__virtualname__ = "bundlefs"

# Cache for vendor paths
_CACHE = {
    'vendor_roots': None,
    'config_path': None,
}


def _find_project_config() -> Optional[Path]:
    """Find project config file."""
    if _CACHE['config_path'] and _CACHE['config_path'].exists():
        return _CACHE['config_path']

    # Try getting from __opts__
    opts = globals().get("__opts__", {})
    if opts:
        config_dir = Path(opts.get("config_dir", "")).parent
        cfg = config_dir / "Saltfile"
        if cfg.exists():
            _CACHE['config_path'] = cfg
            return cfg

    # Fallback: search from CWD
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        cfg = parent / "Saltfile"
        if cfg.exists():
            _CACHE['config_path'] = cfg
            return cfg

    return None


def _load_project_config(cfg_path: Path) -> Optional[Dict[str, Any]]:
    """Load project configuration."""
    try:
        from salt_bundle.utils.yaml import load_yaml
        from salt_bundle.dependencies.saltfile_models import SaltfileConfig

        raw = load_yaml(cfg_path)
        model = SaltfileConfig(**raw)
        return model.model_dump()
    except Exception as e:
        log.warning(f"bundlefs: failed to load config {cfg_path}: {e}")
        return None


def _get_vendor_roots() -> List[str]:
    """
    Get list of all formula directories in vendor/.
    Returns absolute paths to each formula.
    """
    if _CACHE['vendor_roots'] is not None:
        return _CACHE['vendor_roots']

    cfg_path = _find_project_config()
    if not cfg_path:
        log.debug("bundlefs: no Saltfile found")
        return []

    cfg = _load_project_config(cfg_path)
    if not cfg:
        return []

    project_dir = cfg_path.parent
    vendor_dir_name = cfg.get("vendor_dir", "vendor")
    vendor_path = project_dir / vendor_dir_name

    if not vendor_path.exists():
        log.warning(f"bundlefs: vendor dir not found: {vendor_path}")
        return []

    roots = [str(package.absolute()) for package in discover_package_paths(vendor_path)]

    if roots:
        formula_names = [Path(r).name for r in roots]
        log.debug(f"bundlefs: discovered formulas: {', '.join(formula_names)}")

    _CACHE['vendor_roots'] = roots
    return roots


# ---------------------------------------------------------
# 1. Virtual name registration
# ---------------------------------------------------------
def __virtual__():
    """
    Return the virtual name if everything is OK.
    """
    return __virtualname__


# ---------------------------------------------------------
# 2. List of environments
# ---------------------------------------------------------
def envs():
    """
    Return list of available environments.
    For simplicity, we only support 'base' environment.
    """
    return ['base']


# ---------------------------------------------------------
# 3. Find file in fileserver
# ---------------------------------------------------------
def find_file(path, saltenv="base", **kwargs):
    """
    Find a file in the bundlefs fileserver.

    Supports two path formats:
    1. formula_name/file.sls -> vendor/formula_name/file.sls
    2. _states/incus.py -> vendor/incus/_states/incus.py (for Salt module sync)

    Returns dict with path info or empty dict if not found.
    """
    roots = _get_vendor_roots()
    if not roots:
        return {'path': '', 'rel': ''}

    parts = path.split('/', 1)
    if len(parts) < 2:
        return {'path': '', 'rel': ''}

    first_part = parts[0]
    file_name = parts[1]

    # Handle special directories: _states, _modules, etc.
    special_dirs = {'_states', '_modules', '_grains', '_renderers', '_returners',
                    '_runners', '_output', '_utils', '_pillar', '_engines', '_proxy', '_beacons'}

    if first_part in special_dirs:
        # Format: _states/incus.py -> search in all formulas
        namespace = first_part[1:]

        # Try to find the file in any formula
        for root in roots:
            namespace_dir = resolve_namespace_dir(
                Path(root), detect_package_type(Path(root)), namespace
            )
            if namespace_dir is None:
                continue
            full_path = namespace_dir / file_name
            if full_path.is_file():
                stat = full_path.stat()
                return {
                    'path': str(full_path),
                    'rel': path,
                    'stat': tuple(stat),
                    'back': 'bundlefs',
                }
    else:
        # Standard formula file lookup: formula_name/file
        formula_name = first_part
        file_path = file_name

        for root in roots:
            if Path(root).name == formula_name:
                full_path = os.path.join(root, file_path)
                if os.path.isfile(full_path):
                    stat = os.stat(full_path)
                    return {
                        'path': full_path,
                        'rel': path,
                        'stat': tuple(stat),
                        'back': 'bundlefs',
                    }

    return {'path': '', 'rel': ''}


# ---------------------------------------------------------
# 4. List all files
# ---------------------------------------------------------
def file_list(load):
    """
    Return list of all files in the fileserver.

    Special handling:
    - vendor/formula/_states/incus.py -> _states/incus.py (for Salt auto-sync)
    - vendor/formula/init.sls -> formula/init.sls (normal files)
    """
    result = set()
    roots = _get_vendor_roots()

    # Special directories that should be exposed at root level for Salt auto-sync
    special_dirs = {'_states', '_modules', '_grains', '_renderers', '_returners',
                    '_runners', '_output', '_utils', '_pillar', '_engines', '_proxy', '_beacons'}

    for root in roots:
        package_path = Path(root)
        formula_name = package_path.name
        package_type = detect_package_type(package_path)
        namespace_paths = {
            namespace_path: f"_{namespace}"
            for namespace in (name[1:] for name in special_dirs)
            if (namespace_path := resolve_namespace_dir(package_path, package_type, namespace))
            is not None
        }
        for namespace_path, exposed_namespace in namespace_paths.items():
            for file_path in namespace_path.rglob("*"):
                if file_path.is_file():
                    result.add(
                        f"{exposed_namespace}/{file_path.relative_to(namespace_path).as_posix()}"
                    )

        for dirpath, directories, filenames in os.walk(root):
            directories[:] = [
                directory
                for directory in directories
                if Path(dirpath, directory) not in namespace_paths
            ]

            # Check if we're in a special directory
            for filename in filenames:
                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, root)
                # Regular files with formula prefix: formula/init.sls
                result.add(f"{formula_name}/{rel}")

    return sorted(result)


# ---------------------------------------------------------
# 5. List all directories
# ---------------------------------------------------------
def dir_list(load):
    """
    Return list of all directories in the fileserver.
    """
    result = set()
    roots = _get_vendor_roots()

    for root in roots:
        package_path = Path(root)
        namespace_paths = {
            namespace_path: f"_{namespace}"
            for namespace in ("states", "modules", "grains", "renderers", "returners",
                              "runners", "output", "utils", "pillar", "engines", "proxy", "beacons")
            if (namespace_path := resolve_namespace_dir(
                package_path, detect_package_type(package_path), namespace
            )) is not None
        }
        for dirpath, directories, _ in os.walk(root):
            directories[:] = [
                directory
                for directory in directories
                if Path(dirpath, directory) not in namespace_paths
            ]
            rel = os.path.relpath(dirpath, root)
            if rel != '.':
                result.add(rel)
        result.update(namespace_paths.values())

    return sorted(result)


# ---------------------------------------------------------
# 6. File hash (optional but recommended)
# ---------------------------------------------------------
def file_hash(load, fnd):
    """
    Return the hash of a file.
    Required for Salt's caching mechanism.
    """
    if not fnd or 'path' not in fnd or not fnd['path']:
        return {}

    path = fnd['path']
    if not os.path.isfile(path):
        return {}

    try:
        import hashlib
        hash_type = globals().get("__opts__", {}).get(
            "hash_type", load.get("hash_type", "sha256")
        )

        with open(path, 'rb') as f:
            h = hashlib.new(hash_type)
            h.update(f.read())
            return {'hsum': h.hexdigest(), 'hash_type': hash_type}
    except Exception as e:
        log.error(f"bundlefs: failed to hash {path}: {e}")
        return {}


# ---------------------------------------------------------
# 7. Serve file (optional but recommended)
# ---------------------------------------------------------
def serve_file(load, fnd):
    """
    Return a chunk from a file based on the data received.
    Salt reads files in chunks for efficiency.
    """
    ret = {'data': '', 'dest': ''}

    if not fnd or 'path' not in fnd or not fnd['path']:
        return ret

    path = fnd['path']
    if not os.path.isfile(path):
        return ret

    ret['dest'] = fnd.get('rel', '')

    try:
        # Get file buffer size from opts (default 262144 bytes = 256KB)
        buffer_size = globals().get("__opts__", {}).get("file_buffer_size", 262144)

        # Get starting position (loc) from load
        loc = load.get('loc', 0)

        with open(path, 'rb') as fp:
            fp.seek(loc)
            ret['data'] = fp.read(buffer_size)

    except Exception as e:
        log.error(f"bundlefs: failed to read {path}: {e}")

    return ret


# ---------------------------------------------------------
# 8. Update function (required for some Salt versions)
# ---------------------------------------------------------
def update():
    """
    Update fileserver cache.
    This is called periodically by Salt.
    """
    # Clear cache to force re-scan
    _CACHE['vendor_roots'] = None
    return True
