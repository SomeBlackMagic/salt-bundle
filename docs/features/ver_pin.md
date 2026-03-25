# Pin version

## gitfs

Version pinning in gitfs is achieved by configuring a specific **Git tag or commit SHA** as the tracked ref for a Salt environment. For example, setting `gitfs_saltenv` to map `base` to `refs/tags/v1.2.0` pins the `base` environment to that tag. This approach works but is fragile: tags can be moved or deleted in the remote repository without gitfs detecting the change until the next fetch. There is no per-formula pinning — all formulas in a repository are at the same ref, so pinning one formula means pinning all formulas in that repo together. Pinning is also not expressed in any project-level file; it lives exclusively in the Salt master configuration.

## spm

spm supports version pinning via the **explicit version argument** to the install command: `spm install formula=2.3`. Once installed, the specific version's files remain on disk until overwritten. However, this pinning is imperative and not declarative — there is no project manifest file that records "I want formula at version 2.3". If the system is reprovisioned, there is no automated way to re-install the same version without manually specifying it again. The `spm.conf` can list package version preferences but this is not widely used in practice.

## salt-bundle

Version pinning is a **first-class feature** of salt-bundle, expressed declaratively in `.salt-dependencies.yaml`. A dependency entry like `nginx: "1.2.3"` pins to an exact version; the `resolver.matches_constraint()` function in `resolver.py` handles exact match as a special case (no constraint operator present). After `salt-bundle project update`, the resolved exact version is written to `.salt-dependencies.lock` with its SHA256 digest, providing a two-layer pin: the constraint in the manifest pins the logical version, and the digest in the lock file pins the exact binary artifact. Running `salt-bundle project install` from the lock file guarantees the pinned version regardless of what is currently published in the repository.
