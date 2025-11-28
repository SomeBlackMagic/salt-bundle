__virtualname__ = "saltbundle"

def __virtual__():
    return __virtualname__

from pathlib import Path
import logging

log = logging.getLogger(__name__)

def ext_pillar(minion_id, pillar, *args, **kwargs):
    # Import functions from loader.py
    from salt_bundle.ext.loader import (
        _find_project_config,
        _load_project_config,
        _get_formula_paths,
    )

    cfg = _find_project_config()
    if not cfg:
        return {}

    data = _load_project_config(cfg)
    if not data:
        return {}

    project_dir = cfg.parent
    vendor_dir = data.get("vendor_dir", "vendor")
    formulas = _get_formula_paths(project_dir, vendor_dir)

    return {
        "saltbundle": {
            "project_dir": str(project_dir),
            "vendor_dir": vendor_dir,
            "formulas": [f.name for f in formulas],
            "formula_paths": [str(f) for f in formulas],
        }
    }
