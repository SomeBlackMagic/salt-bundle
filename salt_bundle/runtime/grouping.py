"""Group targets that can share the same activated runtime."""

from dataclasses import dataclass
import logging

from salt_bundle.activation.manifest import RuntimeManifest, build_manifest
from salt_bundle.activation.resolver import ActivationResolver


log = logging.getLogger(__name__)


@dataclass
class RuntimeGroup:
    """Targets sharing one immutable runtime manifest."""

    fingerprint: str
    targets: list[str]
    manifest: RuntimeManifest


def group_targets_by_runtime(
    targets: list[str],
    resolver: ActivationResolver,
    *,
    saltenv: str = "base",
) -> dict[str, RuntimeGroup]:
    """Group targets by the fingerprint of their resolved runtime manifest."""
    groups: dict[str, RuntimeGroup] = {}
    for target in targets:
        active_set = resolver.resolve(target, saltenv=saltenv)
        manifest = build_manifest(active_set)
        group = groups.get(manifest.fingerprint)
        if group is None:
            groups[manifest.fingerprint] = RuntimeGroup(
                fingerprint=manifest.fingerprint,
                targets=[target],
                manifest=manifest,
            )
        else:
            group.targets.append(target)

    for group in groups.values():
        group.targets.sort()
    log.debug("SaltBundle runtime grouping: runtime_groups=%s", len(groups))
    return groups
