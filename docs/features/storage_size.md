# Storage Size

## gitfs

gitfs cache size is typically large and grows unboundedly. The bare clone includes the full object database of the remote repository: all historical commits, trees, blobs, and pack files. A formula repository with years of history can consume hundreds of megabytes per remote. Fetching many remotes (one per formula in a typical multi-formula setup) multiplies this cost. There is no built-in mechanism to shallow-clone or prune old objects from the gitfs cache without manual intervention.

## spm

spm storage size is moderate. Installed files go into `extmods/` which contains only the current version of each package — no history, no archives. The download cache under `/var/cache/spm/` holds the last-downloaded `.spm` packages but is not automatically purged. In practice the footprint is proportional to the sum of the current installed package sizes, which is smaller than a full git history.

## salt-bundle

salt-bundle storage is explicitly controlled and predictable. The `vendor/` directory contains only the unpacked content of the currently installed formula versions — no git objects, no historical blobs. The separate download cache (`~/.cache/salt-bundle/packages/`) stores `.tgz` archives keyed by SHA256 digest; archives are reused across projects and versions without duplication. Because formulas are distributed as minimal tarballs (only the files collected by `collect_files()` in `utils/fs.py`), and because the `vendor/` directory can be wiped and regenerated deterministically from the lock file, its size is both small and predictable. The `clear_vendor_dir()` function in `vendor.py` provides an explicit cleanup primitive.
