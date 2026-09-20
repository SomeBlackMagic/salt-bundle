# Offline operation

## gitfs

gitfs cannot operate offline. The Salt master requires network access to Git remotes to fetch updates. If the configured Git server is unreachable, the fileserver falls back to the last successfully cached content, but this fallback behavior is not guaranteed across all Salt versions and configurations. Any branch or tag that has not yet been fetched will be unavailable. gitfs is fundamentally a runtime-pull model and is unsuitable for air-gapped environments.

## spm

spm supports offline operation after packages have been installed. Once an `.spm` archive is installed onto the master or minion, the resulting files are static on the local filesystem and do not require network access at runtime. Installation itself does require access to the spm repository server, but this can be done in advance. For fully air-gapped environments, `.spm` files can be transferred manually and installed from local paths using `spm local install /path/to/package.spm`.

## salt-bundle

salt-bundle supports fully offline operation after the initial install step. The `vendor/` directory contains complete unpacked package trees, and the fileserver and loader integrations operate entirely from the local filesystem. `download_package()` in `dependencies/index.py` caches downloaded `.tgz` archives in `~/.cache/salt-bundle/packages/`, keyed by SHA256 digest. Subsequent installs of the same locked version work without network access when that archive is cached. In air-gapped environments, pre-populate the cache or commit the vendor directory where appropriate.
