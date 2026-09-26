"""Target matching and package collection for activation rules."""

from fnmatch import fnmatchcase

from salt_bundle.activation.models import PackageName
from salt_bundle.activation.parser import TopBundleRule


def match_target(target: str, expression: str) -> bool:
    """Return whether a target matches an exact or shell-style glob expression."""
    return fnmatchcase(target, expression)


def find_matching_rules(
    target: str, rules: list[TopBundleRule]
) -> list[TopBundleRule]:
    """Return matching rules in their declaration order."""
    return [rule for rule in rules if match_target(target, rule.target_expr)]


def collect_packages(matched_rules: list[TopBundleRule]) -> list[PackageName]:
    """Collect packages once, preserving their first occurrence order."""
    packages: list[PackageName] = []
    seen: set[PackageName] = set()
    for rule in matched_rules:
        for package in rule.packages:
            if package not in seen:
                seen.add(package)
                packages.append(package)
    return packages
