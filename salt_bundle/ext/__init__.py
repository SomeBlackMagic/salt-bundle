"""
Salt-Bundle integration package.

This module automatically patches Salt's file_roots on import
to include vendor formulas.
"""
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def _auto_patch_file_roots():
    """
    Automatically add vendor formulas to file_roots on import.
    """
    try:
        from .loader import _find_project_config, _load_project_config, _get_formula_paths

        cfg_path = _find_project_config()
        if not cfg_path:
            return

        cfg = _load_project_config(cfg_path)
        if not cfg:
            return

        project_dir = cfg_path.parent
        vendor_dir = cfg.get("vendor_dir", "vendor")
        formulas = _get_formula_paths(project_dir, vendor_dir)

        if not formulas:
            return

        # Patch global __opts__ if available
        import sys
        for name, module in sys.modules.items():
            if hasattr(module, '__opts__') and isinstance(getattr(module, '__opts__'), dict):
                opts = getattr(module, '__opts__')
                if 'file_roots' in opts:
                    if 'base' not in opts['file_roots']:
                        opts['file_roots']['base'] = []

                    # Add paths if not already present
                    for formula in formulas:
                        path_str = str(formula.absolute())
                        if path_str not in opts['file_roots']['base']:
                            opts['file_roots']['base'].append(path_str)
                            log.debug(f"SaltBundle: auto-added {path_str} to file_roots")

    except Exception as e:
        # Ignore errors - we might not be in Salt environment
        log.debug(f"SaltBundle: auto-patch skipped: {e}")


# Call patch on module import
_auto_patch_file_roots()
