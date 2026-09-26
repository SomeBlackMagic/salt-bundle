"""Resolve the optional runtime manifest supplied to Salt loader callbacks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from salt_bundle.activation.manifest import RuntimeManifest, load_manifest


_MANIFEST_OPTION = "salt_bundle_runtime_manifest"
_MANIFEST_PATH_OPTION = "salt_bundle_runtime_manifest_path"


def get_manifest(opts: Mapping[str, Any] | None = None) -> RuntimeManifest | None:
    """Return the manifest explicitly supplied in Salt opts, if any."""
    if not opts:
        return None

    manifest = opts.get(_MANIFEST_OPTION)
    if manifest is not None:
        if not isinstance(manifest, RuntimeManifest):
            raise TypeError(
                f"Salt option '{_MANIFEST_OPTION}' must be a RuntimeManifest"
            )
        return manifest

    manifest_path = opts.get(_MANIFEST_PATH_OPTION)
    if manifest_path is None:
        return None
    return load_manifest(Path(manifest_path))
