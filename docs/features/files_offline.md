# Offline operation

## gitfs

gitfs cannot operate offline. The Salt master requires network access to Git remotes to fetch updates. If the configured Git server is unreachable, the fileserver falls back to the last successfully cached content, but this fallback behavior is not guaranteed across all Salt versions and configurations. Any branch or tag that has not yet been fetched will be unavailable. gitfs is fundamentally a runtime-pull model and is unsuitable for air-gapped environments.

## spm

spm supports offline operation after packages have been installed. Once an `.spm` archive is installed onto the master or minion, the resulting files are static on the local filesystem and do not require network access at runtime. Installation itself does require access to the spm repository server, but this can be done in advance. For fully air-gapped environments, `.spm` files can be transferred manually and installed from local paths using `spm local install /path/to/package.spm`.

## salt-bundle

salt-bundle supports fully offline operation after the initial install step. The `vendor/` directory contains complete unpacked formula trees, and both the `bundlefs` fileserver backend and the `ext/loader.py` hooks operate entirely from the local filesystem without any network calls. The `download_package()` function in `repository.py` caches downloaded `.tgz` archives in `~/.cache/salt-bundle/packages/` (XDG-compliant path from `config.py`), keyed by the SHA256 digest. This means subsequent installs of the same version also work without network access if the package is already in the local cache. In air-gapped environments, the cache directory can be pre-populated and the `vendor/` directory committed to version control.
