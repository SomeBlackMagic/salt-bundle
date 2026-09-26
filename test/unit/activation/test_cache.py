"""Tests for runtime activation caches."""

import importlib.util
from pathlib import Path
import tempfile
from threading import Barrier, Thread
import unittest

from salt_bundle.activation.manifest import ManifestPackageEntry, RuntimeManifest
from salt_bundle.activation.models import ActivePackageSet, PackageName, ResolvedPackage


class TestRuntimeCache(unittest.TestCase):
    """Specify cache isolation and invalidation for activated runtimes."""

    def _cache_module(self):
        spec = importlib.util.find_spec("salt_bundle.activation.cache")
        self.assertIsNotNone(
            spec,
            "activation must provide a runtime cache module",
        )

        from salt_bundle.activation import cache

        return cache

    @staticmethod
    def _manifest(fingerprint: str = "a" * 64) -> RuntimeManifest:
        return RuntimeManifest(
            schema_version=1,
            saltenv="base",
            fingerprint=fingerprint,
            packages=(
                ManifestPackageEntry(
                    name=PackageName.parse("acme/nginx"),
                    version="1.2.0",
                    package_type="formula",
                    digest="sha256:nginx",
                    path="vendor/acme/nginx",
                ),
            ),
        )

    @staticmethod
    def _resolution(fingerprint: str = "a" * 64) -> ActivePackageSet:
        return ActivePackageSet(
            target="web-01",
            saltenv="base",
            fingerprint=fingerprint,
            packages=(
                ResolvedPackage(
                    name=PackageName.parse("acme/nginx"),
                    version="1.2.0",
                    package_type="formula",
                    path=Path("vendor/acme/nginx"),
                    digest="sha256:nginx",
                ),
            ),
        )

    def test_manifest_cache_misses_before_a_manifest_is_stored(self) -> None:
        cache_module = self._cache_module()

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))

            self.assertIsNone(cache.get_manifest("a" * 64))

    def test_manifest_cache_persists_and_loads_by_fingerprint(self) -> None:
        cache_module = self._cache_module()
        manifest = self._manifest()

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))
            cache.put_manifest(manifest)

            self.assertEqual(cache.get_manifest(manifest.fingerprint), manifest)
            self.assertTrue(
                (Path(directory) / "runtimes" / manifest.fingerprint / "manifest.yaml").is_file()
            )

    def test_manifest_cache_does_not_return_a_different_fingerprint(self) -> None:
        cache_module = self._cache_module()

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))
            cache.put_manifest(self._manifest("a" * 64))

            self.assertIsNone(cache.get_manifest("b" * 64))

    def test_resolution_cache_misses_before_a_result_is_stored(self) -> None:
        cache_module = self._cache_module()

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))

            self.assertIsNone(cache.get_resolution("resolution-key"))

    def test_resolution_cache_returns_a_result_for_its_exact_key(self) -> None:
        cache_module = self._cache_module()
        resolution = self._resolution()

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))
            cache.put_resolution("resolution-key", resolution)

            self.assertEqual(cache.get_resolution("resolution-key"), resolution)
            self.assertIsNone(cache.get_resolution("other-resolution-key"))

    def test_invalidate_removes_manifest_and_in_memory_cache_entries(self) -> None:
        cache_module = self._cache_module()
        manifest = self._manifest()
        resolution = self._resolution()

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))
            cache.put_manifest(manifest)
            cache.put_resolution("resolution-key", resolution)
            cache.put_loader_dirs(manifest.fingerprint, "modules", (Path("_modules"),))

            cache.invalidate()

            self.assertIsNone(cache.get_manifest(manifest.fingerprint))
            self.assertIsNone(cache.get_resolution("resolution-key"))
            self.assertIsNone(cache.get_loader_dirs(manifest.fingerprint, "modules"))

    def test_resolution_cache_key_changes_for_each_runtime_input(self) -> None:
        cache_module = self._cache_module()
        baseline = cache_module.compute_resolution_cache_key(
            "top-digest-a", "lock-digest-a", "web-01", "base"
        )

        variants = (
            ("top-digest-b", "lock-digest-a", "web-01", "base"),
            ("top-digest-a", "lock-digest-b", "web-01", "base"),
            ("top-digest-a", "lock-digest-a", "web-02", "base"),
            ("top-digest-a", "lock-digest-a", "web-01", "dev"),
        )

        for values in variants:
            with self.subTest(values=values):
                self.assertNotEqual(
                    baseline,
                    cache_module.compute_resolution_cache_key(*values),
                )

    def test_loader_dirs_are_keyed_by_fingerprint_and_module_type(self) -> None:
        cache_module = self._cache_module()

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))
            module_paths = (Path("vendor/acme/nginx/_modules"),)
            state_paths = (Path("vendor/acme/nginx/_states"),)
            cache.put_loader_dirs("a" * 64, "modules", module_paths)
            cache.put_loader_dirs("a" * 64, "states", state_paths)

            self.assertEqual(cache.get_loader_dirs("a" * 64, "modules"), module_paths)
            self.assertEqual(cache.get_loader_dirs("a" * 64, "states"), state_paths)
            self.assertIsNone(cache.get_loader_dirs("b" * 64, "modules"))

    def test_concurrent_manifest_writes_do_not_corrupt_cached_content(self) -> None:
        cache_module = self._cache_module()
        manifests = (self._manifest("a" * 64), self._manifest("b" * 64))

        with tempfile.TemporaryDirectory() as directory:
            cache = cache_module.RuntimeCache(Path(directory))
            barrier = Barrier(len(manifests))
            failures: list[BaseException] = []

            def store(manifest: RuntimeManifest) -> None:
                try:
                    barrier.wait()
                    cache.put_manifest(manifest)
                except BaseException as exc:  # pragma: no cover - asserted below
                    failures.append(exc)

            threads = [Thread(target=store, args=(manifest,)) for manifest in manifests]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            self.assertEqual(failures, [])
            for manifest in manifests:
                self.assertEqual(cache.get_manifest(manifest.fingerprint), manifest)
