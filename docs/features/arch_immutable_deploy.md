# Immutable deploy

## gitfs

gitfs does **not** support immutable deployments. Because the Salt master continuously pulls from the upstream Git remote, the formula content available to minions can change at any time without an explicit deployment action. A commit pushed to the tracked branch will be reflected in formula execution as soon as the master's next fetch cycle completes. There is no mechanism to freeze the deployed state — even if a tag is configured as the source, someone can move or delete the tag and the master will not detect the discrepancy. Rollback requires manually resetting the tracked ref and waiting for the next pull.

## spm

spm provides **partial** immutability. Once a `.spm` package is installed, its files remain on disk until explicitly removed or overwritten by a newer install. The installed files themselves do not change spontaneously. However, immutability is not enforced — there is no integrity check after installation, no digest verification of the installed files, and running `spm install` again with a different version silently replaces the previous one. There is also no record of which repository version was used, so verifying that the deployed state matches a specific release is not possible without external tooling.

## salt-bundle

salt-bundle **fully supports** immutable deployments. Every installed package's exact version, source repository, download URL, and SHA256 digest is recorded in `.salt-dependencies.lock`. The `download_package` function in `repository.py` verifies the digest on every download using `verify_digest()`, and the cache key is derived from the digest hash itself (`cache_dir / f"{digest_hash}.tgz"`). Running `salt-bundle project install` on any machine with the same lock file produces a byte-for-byte identical vendor directory. The vendor directory, once populated, is not modified by Salt at runtime — it is read-only from Salt's perspective. For local `type: path` repositories, the `digest` field is set to the literal string `"path"` and the package directory is symlinked rather than copied, which is the only case where strict immutability does not apply.
