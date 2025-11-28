import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache

log = logging.getLogger(__name__)

# Cache for results to avoid rescanning on every call
_CACHE = {
    'config_path': None,
    'config_mtime': None,
    'config_data': None,
    'formulas': None,
}


def _find_project_config():
    """Find project config (with caching)."""
    # Check cache
    if _CACHE['config_path'] and _CACHE['config_path'].exists():
        return _CACHE['config_path']

    # 1. Search near config_dir
    __opts__ = globals().get("__opts__", {})
    cfg = Path(__opts__.get("config_dir", "")).parent / ".salt-dependencies.yaml"
    if cfg.exists():
        _CACHE['config_path'] = cfg
        return cfg

    # 2. Fallback: CWD + parents
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        candidate = parent / ".salt-dependencies.yaml"
        if candidate.exists():
            _CACHE['config_path'] = candidate
            return candidate

    return None


def _load_project_config(cfg: Path) -> Optional[Dict[str, Any]]:
    """Load project config (with caching by mtime)."""
    try:
        current_mtime = cfg.stat().st_mtime

        # Check cache
        if (_CACHE['config_data'] is not None and
            _CACHE['config_mtime'] == current_mtime):
            return _CACHE['config_data']

        # Load config
        from salt_bundle.utils.yaml import load_yaml
        from salt_bundle.models.config_models import ProjectConfig

        raw = load_yaml(cfg)
        model = ProjectConfig(**raw)
        data = model.model_dump()

        # Save to cache
        _CACHE['config_data'] = data
        _CACHE['config_mtime'] = current_mtime

        return data
    except Exception as e:
        log.warning(f"SaltBundle: failed loading config {cfg}: {e}")
        return None


def _get_formula_paths(project_dir: Path, vendor_dir: str) -> List[Path]:
    """Get paths to formulas (with caching)."""
    # Check cache
    if _CACHE['formulas'] is not None:
        return _CACHE['formulas']

    root = project_dir / vendor_dir
    if not root.exists():
        return []

    out = []
    for item in root.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            out.append(item)

    if out:
        formula_names = [f.name for f in out]
        log.debug(f"SaltBundle: discovered formulas: {', '.join(formula_names)}")

    # Save to cache
    _CACHE['formulas'] = out

    return out


# ───────────────────────────────────────────────
#  FILE_ROOTS LOADER HOOK
# ───────────────────────────────────────────────

@lru_cache(maxsize=32)
def _get_module_dirs(formula_type: str) -> tuple:
    """
    Get paths to modules of specified type from all formulas (with caching).
    formula_type: 'modules', 'states', 'grains', etc.
    Returns tuple for lru_cache compatibility.
    """
    cfg_path = _find_project_config()
    if not cfg_path:
        return tuple()

    cfg = _load_project_config(cfg_path)
    if not cfg:
        return tuple()

    project_dir = cfg_path.parent
    vendor_dir = cfg.get("vendor_dir", "vendor")
    formulas = _get_formula_paths(project_dir, vendor_dir)

    paths = []
    found_formulas = []
    found_modules = []

    for formula in formulas:
        mod_dir = formula / f"_{formula_type}"
        if mod_dir.exists() and mod_dir.is_dir():
            paths.append(str(mod_dir.absolute()))
            found_formulas.append(formula.name)

            # Collect list of modules/states in directory
            modules = [f.stem for f in mod_dir.glob("*.py") if f.name != "__init__.py"]
            found_modules.extend(modules)

    if paths:
        log.debug(
            f"SaltBundle: loaded _{formula_type} from formulas: {', '.join(found_formulas)} "
            f"(modules: {', '.join(found_modules)})"
        )

    return tuple(paths)


# Entry points for Salt loader
def module_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _modules directories in vendor formulas."""
    return list(_get_module_dirs("modules"))


def states_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _states directories in vendor formulas."""
    return list(_get_module_dirs("states"))


def grains_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _grains directories in vendor formulas."""
    return list(_get_module_dirs("grains"))


def pillar_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _pillar directories in vendor formulas."""
    return list(_get_module_dirs("pillar"))


def returner_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _returners directories in vendor formulas."""
    return list(_get_module_dirs("returners"))


def runner_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _runners directories in vendor formulas."""
    return list(_get_module_dirs("runners"))


def outputter_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _output directories in vendor formulas."""
    return list(_get_module_dirs("output"))


def utils_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _utils directories in vendor formulas."""
    return list(_get_module_dirs("utils"))


def render_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _renderers directories in vendor formulas."""
    return list(_get_module_dirs("renderers"))


def engines_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _engines directories in vendor formulas."""
    return list(_get_module_dirs("engines"))


def proxy_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _proxy directories in vendor formulas."""
    return list(_get_module_dirs("proxy"))


def beacons_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _beacons directories in vendor formulas."""
    return list(_get_module_dirs("beacons"))


def fileserver_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _fileserver directories in vendor formulas and bundlefs."""
    paths = list(_get_module_dirs("fileserver"))

    # Add bundlefs from salt_bundle package itself
    bundlefs_path = Path(__file__).parent / "fileserver"
    if bundlefs_path.exists():
        paths.append(str(bundlefs_path.absolute()))
        log.debug(f"SaltBundle: added bundlefs fileserver from {bundlefs_path}")

    return paths


def configure(opts: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Automatically register vendor_dir as an additional file_root.

    This makes formulas in vendor/* visible to Salt file server
    (salt, salt-call --local, salt-ssh).
    """
    if opts is None:
        opts = globals().get("__opts__", {})

    # Locate project configuration
    cfg_path = _find_project_config()
    if not cfg_path:
        return opts

    cfg = _load_project_config(cfg_path)
    if not cfg:
        return opts

    # Compute vendor path
    project_dir = cfg_path.parent
    vendor_dir_name = cfg.get("vendor_dir", "vendor")
    vendor_path = (project_dir / vendor_dir_name).resolve()

    if not vendor_path.exists():
        log.warning(f"SaltBundle: vendor_dir not found: {vendor_path}")
        return opts

    # Prepare file_roots structure
    file_roots = opts.get("file_roots")
    if not isinstance(file_roots, dict):
        file_roots = {"base": []}

    # Get base roots as a copy
    base_roots = list(file_roots.get("base", []))

    # Register vendor dir if not already present
    vpath_str = str(vendor_path)
    if vpath_str not in base_roots:
        base_roots.append(vpath_str)
        log.debug(f"SaltBundle: added vendor_dir to file_roots: {vpath_str}")

    # Save back into opts
    file_roots["base"] = base_roots
    opts["file_roots"] = file_roots

    return opts

