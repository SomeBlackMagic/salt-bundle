import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache

from salt_bundle.salt import runtime_context
from salt_bundle.package_layout import (
    detect_package_type,
    discover_package_paths,
    resolve_namespace_dir,
)

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
    cfg = Path(__opts__.get("config_dir", "")).parent / "Saltfile"
    if cfg.exists():
        _CACHE['config_path'] = cfg
        return cfg

    # 2. Fallback: CWD + parents
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        candidate = parent / "Saltfile"
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
        from salt_bundle.dependencies.saltfile_models import SaltfileConfig

        raw = load_yaml(cfg)
        model = SaltfileConfig(**raw)
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

    out = discover_package_paths(root)

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
        mod_dir = resolve_namespace_dir(
            formula, detect_package_type(formula), formula_type
        )
        if mod_dir is not None:
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


@lru_cache(maxsize=256)
def _get_manifest_dirs(
    namespace: str,
    fingerprint: str,
    package_paths: tuple[str, ...],
) -> tuple[str, ...]:
    """Return namespace directories cached by runtime manifest fingerprint."""
    del fingerprint
    return tuple(
        str(namespace_path)
        for package_path in package_paths
        if (namespace_path := resolve_namespace_dir(
            Path(package_path), detect_package_type(Path(package_path)), namespace
        )) is not None
    )


def _get_loader_dirs(opts: Dict[str, Any] | None, namespace: str) -> tuple[str, ...]:
    """Get active runtime directories, or preserve legacy global activation."""
    effective_opts = opts if opts is not None else globals().get("__opts__", {})
    manifest = runtime_context.get_manifest(effective_opts)
    if manifest is None:
        return _get_module_dirs(namespace)
    return _get_manifest_dirs(
        namespace,
        manifest.fingerprint,
        tuple(
            str(_resolve_manifest_package_path(package.path, effective_opts))
            for package in manifest.packages
        ),
    )


def _resolve_manifest_package_path(path: str, opts: Dict[str, Any]) -> Path:
    """Resolve a portable manifest path in the local minion project tree."""
    package_path = Path(path)
    if package_path.is_absolute():
        return package_path
    project_root = opts.get("salt_bundle_runtime_project_root")
    return Path(project_root) / package_path if project_root else package_path


# Entry points for Salt loader
def module_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _modules directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "modules"))


def auth_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _auth directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "auth"))


def states_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _states directories in vendor formulas."""
    result = list(_get_loader_dirs(opts, "states"))
    # log.debug(f"SaltBundle: states_dirs() called, returning {len(result)} paths: {result}")
    return result


def cache_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _cache directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "cache"))


def executor_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _executors directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "executors"))


def grains_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _grains directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "grains"))


def log_handlers_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _log_handlers directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "log_handlers"))


def matchers_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _matchers directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "matchers"))


def metaproxy_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _metaproxy directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "metaproxy"))


def netapi_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _netapi directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "netapi"))


def pillar_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _pillar directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "pillar"))


def queue_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _queues directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "queues"))


def returner_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _returners directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "returners"))


def roster_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _roster directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "roster"))


def runner_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _runners directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "runners"))


def sdb_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _sdb directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "sdb"))


def serializers_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _serializers directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "serializers"))


def outputter_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _output directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "output"))


def pkgdb_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _pkgdb directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "pkgdb"))


def pkgfiles_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _pkgfiles directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "pkgfiles"))


def top_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _tops directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "tops"))


def utils_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _utils directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "utils"))


def wrapper_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _wrapper directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "wrapper"))


def render_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _renderers directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "renderers"))


def engines_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _engines directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "engines"))


def proxy_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _proxy directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "proxy"))


def cloud_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _clouds directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "clouds"))


def beacons_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _beacons directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "beacons"))


def thorium_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _thorium directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "thorium"))


def tokens_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _tokens directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "tokens"))


def wheel_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _wheel directories in vendor formulas."""
    return list(_get_loader_dirs(opts, "wheel"))


def fileserver_dirs(opts: Dict[str, Any] = None) -> List[str]:
    """Return paths to _fileserver directories in vendor formulas and bundlefs."""
    paths = list(_get_loader_dirs(opts, "fileserver"))

    # Add bundlefs from salt_bundle package itself
    bundlefs_path = Path(__file__).parent / "fileserver"
    if bundlefs_path.exists():
        paths.append(str(bundlefs_path.absolute()))
        #log.debug(f"SaltBundle: added bundlefs fileserver from {bundlefs_path}")

    return paths


def configure(opts: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Configure Salt options for vendor formulas.

    NOTE: We do NOT add vendor_dir to file_roots because this causes
    Salt to recursively copy _modules and _states directories into cache,
    creating infinite nesting (modules/modules/modules/...).

    Instead, modules and states are loaded via module_dirs() and states_dirs()
    hooks, which Salt's loader calls directly.
    """
    if opts is None:
        opts = globals().get("__opts__", {})

    # Just return opts without modification
    # Module/state loading is handled by module_dirs() and states_dirs()
    return opts
