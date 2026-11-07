"""Add the SLS of matched SaltBundle formulas to Salt's top data."""

from pathlib import Path

from salt_bundle.activation.matcher import collect_packages, find_matching_rules
from salt_bundle.activation.parser import load_top_bundle
from salt_bundle.activation.resolver import ActivationResolver
from salt_bundle.dependencies.lockfile import load_lockfile
from salt_bundle.dependencies.saltfile import load_saltfile
from salt_bundle.package_layout import resolve_formula_sls_name
from salt_bundle.storage.vendor import get_vendor_dir


__virtualname__ = "salt_bundle"


def __virtual__():
    return __virtualname__


def _project_dir(opts):
    config_dir = opts.get("config_dir")
    if config_dir:
        config_path = Path(config_dir).resolve()
        for parent in (config_path, *config_path.parents):
            if (parent / "Saltfile").is_file():
                return parent
    current = Path.cwd()
    for parent in (current, *current.parents):
        if (parent / "Saltfile").is_file():
            return parent
    return None


def top(**kwargs):
    """Return matched formula SLS names for one Salt SSH target."""
    opts = kwargs.get("opts") or globals().get("__opts__", {})
    target = opts.get("id")
    project_dir = _project_dir(opts)
    if not target or project_dir is None:
        return {}

    config = load_saltfile(project_dir)
    top_path = project_dir / config.runtime.top_bundle_file
    if not top_path.is_file():
        if config.runtime.require_bundle_top:
            raise FileNotFoundError(f"Required top bundle does not exist: {top_path}")
        return {}

    bundle_top = load_top_bundle(top_path)
    vendor_root = get_vendor_dir(project_dir, config.vendor_dir)
    resolver = ActivationResolver(
        top_bundle=bundle_top,
        lock_data=load_lockfile(project_dir),
        vendor_root=vendor_root,
        require_bundle_top=config.runtime.require_bundle_top,
        top_bundle_path=top_path,
    )
    result = {}
    for saltenv, environment in bundle_top.environments.items():
        matched = collect_packages(find_matching_rules(target, environment.rules))
        if not matched:
            continue
        active = resolver.resolve(target, saltenv=saltenv)
        direct = {name.full_name for name in matched}
        states = [
            resolve_formula_sls_name(package.path)
            for package in active.packages
            if package.package_type == "formula"
            and package.name.full_name in direct
        ]
        if states:
            result[saltenv] = states
    return result
