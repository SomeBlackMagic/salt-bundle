# Predictability

## gitfs

gitfs is inherently unpredictable in production. States are fetched from a live Git remote at runtime, so any push to a tracked branch is immediately reflected in the next Salt run. There is no lock mechanism preventing the master from pulling a breaking commit. If a remote branch is force-pushed or a tag is moved, the effective state changes silently. Drift between minions is possible when the master's gitfs cache is partially updated. The only way to pin behavior is to use an immutable tag, but nothing in the tooling enforces this.

## spm

SPM offers moderate predictability. Once a package is installed via `spm install`, the files sit on disk in `extmods/` and do not change unless someone explicitly reinstalls or removes the package. However, the SPM database tracks installed version metadata but does not enforce it — files can be overwritten manually without updating the database. There is no lock file, so running `spm install` again may install a different version if the remote index has been updated. Reproducibility across machines depends on the repository index being stable, which is not guaranteed.

## salt-bundle

salt-bundle is fully predictable by design. After `salt-bundle project update` runs, the resolver writes exact versions, repository names, package URLs, and SHA-256 digests into `.salt-dependencies.lock`. Subsequent `salt-bundle project install` (or `vendor`) reads only from that lock file — it never re-resolves constraints, never queries the index for a newer match, and verifies the downloaded archive against the stored digest. The vendor directory is populated identically on every machine that shares the lock file, regardless of what the upstream repository index contains at that moment.
