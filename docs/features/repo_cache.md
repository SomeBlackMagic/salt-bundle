# Caching

## gitfs

gitfs caches repository content in the Salt master's gitfs cache directory, typically `/var/cache/salt/master/gitfs/`. Each configured remote is cloned into a subdirectory identified by a hash of the remote URL and branch. Subsequent fetches are incremental Git operations (`git fetch`). The cache grows proportionally to the size of the full Git history of all configured remotes. There is no built-in garbage collection for stale gitfs cache entries; removing a remote from `gitfs_remotes` does not automatically clean its cache directory, requiring manual cleanup.

## spm

spm maintains a package cache in a directory configurable via `spm_cache_dir` (typically `/var/cache/salt/spm/`). Downloaded `.spm` archives are stored here before installation. The cache is not content-addressed — packages are stored by filename, so a file with the same name but different content could silently replace a cached entry. There is no built-in mechanism for verifying cached package integrity against a checksum, and no automatic expiry or garbage collection of old versions.

## salt-bundle

salt-bundle uses a content-addressed package cache at `~/.cache/salt-bundle/packages/` (XDG-compliant; overridable via `XDG_CACHE_HOME`). `download_package()` in `dependencies/index.py` derives the cache filename from the SHA256 digest: `{digest_hash}.tgz`. Before downloading, it validates any existing cache entry; a corrupted entry is deleted and downloaded again. This means a given package archive is downloaded at most once per user, regardless of how many projects depend on it. The Salt loader and fileserver integration also cache project discovery during a Salt process lifetime.
