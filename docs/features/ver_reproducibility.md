# Reproducibility

## gitfs

gitfs provides **no reproducibility** guarantees. Two Salt masters configured with the same `gitfs_remotes` pointing to the same branch will serve the same content only as long as the branch HEAD has not moved. Any push to the branch, any tag deletion, or any repository force-push will cause the two masters to diverge the next time they fetch. Even if no changes are made, relying on a branch name means the content definition changes over time. Reproducibility requires external discipline (pinning specific commit SHAs in the master config), not a built-in mechanism.

## spm

spm provides **partial reproducibility**. Installing the same named version of a package (`spm install formula=2.3`) will install the same files — provided the package at that version has not been replaced in the repository. spm does not record a digest of the downloaded package, so it cannot detect if the repository has served a different binary under the same version string. There is also no mechanism to reproduce the complete set of installed packages atomically — each package must be installed individually with its version specified manually.

## salt-bundle

salt-bundle provides **full reproducibility** as a design goal. The combination of the lock file and SHA256 digest verification makes deployments bit-for-bit reproducible:

1. `salt-bundle project update` resolves constraints, selects the best matching version, records the exact version and `sha256:<hex>` digest in `.salt-dependencies.lock`.
2. `salt-bundle project install` reads the lock file, downloads each package, and verifies the digest via `verify_digest()` in `utils/hashing.py` before extracting. If the digest does not match, the download is rejected and the cached file is deleted.
3. The download cache in `~/.cache/salt-bundle/packages/` uses the digest hash as the cache key (`{digest_hash}.tgz`), so a cached file is never confused with a different version.

Any environment that has the same `.salt-dependencies.lock` file and access to the configured repositories will produce an identical vendor directory, regardless of when the install is run or what other versions have been published since.
