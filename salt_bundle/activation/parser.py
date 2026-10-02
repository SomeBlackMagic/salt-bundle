"""Parser for target-aware package activation maps."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from salt_bundle.activation.errors import BundleTopSyntaxError
from salt_bundle.activation.models import PackageName


class _TopBundleLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(loader: _TopBundleLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    """Construct a mapping while rejecting duplicate keys."""
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise BundleTopSyntaxError("Mapping keys must be hashable") from exc
        if duplicate:
            raise BundleTopSyntaxError(f"Duplicate mapping key: {key!r}")
        mapping[key] = loader.construct_object(value_node)
    return mapping


_TopBundleLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


@dataclass(frozen=True)
class TopBundleRule:
    """Packages activated when a target expression matches."""

    target_expr: str
    packages: list[PackageName]


@dataclass(frozen=True)
class TopBundleEnv:
    """Activation rules for one Salt environment."""

    name: str
    rules: list[TopBundleRule]


@dataclass(frozen=True)
class TopBundle:
    """Activation configuration grouped by Salt environment."""

    environments: dict[str, TopBundleEnv]


def parse_top_bundle(content: str) -> TopBundle:
    """Parse YAML content into a target-aware activation map."""
    try:
        raw_top_bundle = yaml.load(content, Loader=_TopBundleLoader)
    except BundleTopSyntaxError:
        raise
    except yaml.YAMLError as exc:
        raise BundleTopSyntaxError("Invalid top_bundle.sls YAML") from exc

    if raw_top_bundle is None:
        raw_top_bundle = {}
    if not isinstance(raw_top_bundle, dict):
        raise BundleTopSyntaxError("top_bundle.sls root must be a mapping")

    environments: dict[str, TopBundleEnv] = {}
    for environment_name, raw_rules in raw_top_bundle.items():
        if not isinstance(environment_name, str):
            raise BundleTopSyntaxError("Environment name must be a string")
        if not isinstance(raw_rules, dict):
            raise BundleTopSyntaxError(
                f"Environment {environment_name!r} must be a mapping"
            )

        rules: list[TopBundleRule] = []
        for target_expr, raw_packages in raw_rules.items():
            if not isinstance(target_expr, str):
                raise BundleTopSyntaxError("Target expression must be a string")
            if not isinstance(raw_packages, list):
                raise BundleTopSyntaxError(
                    f"Packages for target {target_expr!r} must be a list"
                )

            packages = []
            for item in raw_packages:
                if not isinstance(item, str):
                    raise BundleTopSyntaxError(
                        f"Package name must be a string, got {type(item).__name__}: {item!r}"
                    )
                try:
                    packages.append(PackageName.parse(item))
                except ValueError as exc:
                    raise BundleTopSyntaxError(str(exc)) from exc
            if len(set(packages)) != len(packages):
                raise BundleTopSyntaxError(
                    f"Duplicate package in target {target_expr!r}"
                )
            rules.append(TopBundleRule(target_expr=target_expr, packages=packages))

        environments[environment_name] = TopBundleEnv(
            name=environment_name,
            rules=rules,
        )

    return TopBundle(environments=environments)


def load_top_bundle(path: Path) -> TopBundle:
    """Load and parse ``top_bundle.sls`` from ``path``."""
    return parse_top_bundle(path.read_text(encoding="utf-8"))
