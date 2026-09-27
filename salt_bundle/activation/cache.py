"""Caches for target-aware activated Salt runtimes."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from threading import RLock

from .manifest import RuntimeManifest, deserialize_manifest, serialize_manifest
from .models import ActivePackageSet


log = logging.getLogger(__name__)


def compute_resolution_cache_key(
    top_bundle_digest: str,
    lock_digest: str,
    target: str,
    saltenv: str,
) -> str:
    """Return a stable key for one activation resolution input set."""
    content = json.dumps(
        {
            "lock_digest": lock_digest,
            "saltenv": saltenv,
            "target": target,
            "top_bundle_digest": top_bundle_digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class RuntimeCache:
    """Store manifests on disk and process-local activation lookup results."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self._resolutions: dict[str, ActivePackageSet] = {}
        self._loader_dirs: dict[tuple[str, str], tuple[Path, ...]] = {}
        self._lock = RLock()

    def get_manifest(self, fingerprint: str) -> RuntimeManifest | None:
        """Return the cached manifest for ``fingerprint``, if it exists."""
        path = self._manifest_path(fingerprint)
        with self._lock:
            if not path.is_file():
                log.debug(
                    "SaltBundle cache: cache=miss kind=manifest fingerprint=%s",
                    fingerprint,
                )
                return None
            manifest = deserialize_manifest(path.read_text(encoding="utf-8"))
        log.debug(
            "SaltBundle cache: cache=hit kind=manifest fingerprint=%s", fingerprint
        )
        return manifest

    def put_manifest(self, manifest: RuntimeManifest) -> None:
        """Atomically persist ``manifest`` under its runtime fingerprint."""
        path = self._manifest_path(manifest.fingerprint)
        content = serialize_manifest(manifest)
        with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=".manifest-",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_file.write(content)
                temporary_path = Path(temporary_file.name)
            try:
                os.replace(temporary_path, path)
            finally:
                temporary_path.unlink(missing_ok=True)

    def get_resolution(self, cache_key: str) -> ActivePackageSet | None:
        """Return the process-local resolution cached under ``cache_key``."""
        with self._lock:
            return self._resolutions.get(cache_key)

    def put_resolution(self, cache_key: str, result: ActivePackageSet) -> None:
        """Cache an activation resolution for the current Salt process."""
        with self._lock:
            self._resolutions[cache_key] = result

    def get_loader_dirs(
        self, fingerprint: str, module_type: str
    ) -> tuple[Path, ...] | None:
        """Return loader paths for one runtime fingerprint and namespace."""
        with self._lock:
            return self._loader_dirs.get((fingerprint, module_type))

    def put_loader_dirs(
        self,
        fingerprint: str,
        module_type: str,
        paths: tuple[Path, ...],
    ) -> None:
        """Cache immutable loader paths for one runtime fingerprint and namespace."""
        with self._lock:
            self._loader_dirs[(fingerprint, module_type)] = tuple(paths)

    def invalidate(self) -> None:
        """Clear every in-memory entry and persisted runtime manifest."""
        with self._lock:
            self._resolutions.clear()
            self._loader_dirs.clear()
            shutil.rmtree(self.cache_dir / "runtimes", ignore_errors=True)

    def _manifest_path(self, fingerprint: str) -> Path:
        if not fingerprint or Path(fingerprint).name != fingerprint:
            raise ValueError("Runtime fingerprint must be a single path component")
        return self.cache_dir / "runtimes" / fingerprint / "manifest.yaml"
