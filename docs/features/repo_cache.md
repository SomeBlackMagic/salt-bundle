# Caching

## gitfs

gitfs caches repository content in the Salt master's gitfs cache directory, typically `/var/cache/salt/master/gitfs/`. Each configured remote is cloned into a subdirectory identified by a hash of the remote URL and branch. Subsequent fetches are incremental Git operations (`git fetch`). The cache grows proportionally to the size of the full Git history of all configured remotes. There is no built-in garbage collection for stale gitfs cache entries; removing a remote from `gitfs_remotes` does not automatically clean its cache directory, requiring manual cleanup.

## spm

spm maintains a package cache in a directory configurable via `spm_cache_dir` (typically `/var/cache/salt/spm/`). Downloaded `.spm` archives are stored here before installation. The cache is not content-addressed — packages are stored by filename, so a file with the same name but different content could silently replace a cached entry. There is no built-in mechanism for verifying cached package integrity against a checksum, and no automatic expiry or garbage collection of old versions.

## salt-bundle

salt-bundle uses a content-addressed package cache at `~/.cache/salt-bundle/packages/` (XDG-compliant; overridable via `XDG_CACHE_HOME`). The `download_package()` function in `repository.py` derives the cache filename from the SHA256 digest: `{digest_hash}.tgz`, where `digest_hash` is the hex portion of the `sha256:<hex>` string. Before downloading, the function checks whether the cache file already exists and verifies its integrity with `verify_digest()`; a corrupted cache entry is automatically deleted and re-downloaded. This content-addressed scheme means a given package version is downloaded at most once per user, regardless of how many projects depend on it. The `bundlefs` fileserver backend and `ext/loader.py` maintain their own in-process caches (`_CACHE` dicts) keyed on config file mtime, preventing redundant filesystem scans within a single Salt process lifetime.
