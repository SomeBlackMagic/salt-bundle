# Garbage Control

## gitfs

gitfs has no automated garbage collection for its cache. Old pack files, unreachable objects from deleted branches, and stale remote-tracking refs accumulate in the bare clone over time. Manual cleanup requires stopping the Salt master, removing the gitfs cache directory for specific remotes (`$cachedir/gitfs/<hash>/`), and allowing Salt to re-clone on next start. Salt does not expose a `salt-run` command to prune individual gitfs caches selectively.

## spm

spm has limited and partially implemented garbage control. Uninstalling a package with `spm remove <package>` removes its files from `extmods/`, but leftover files from partial installs or files that were present in an older version but removed in a newer one can remain. The download cache at `/var/cache/spm/` is not automatically purged. There is no equivalent of a garbage-collect or prune command that scans for orphaned files across the extmods tree.

## salt-bundle

salt-bundle provides explicit and deterministic garbage control. The `clear_vendor_dir()` function in `vendor.py` removes all contents of `vendor/` in a single operation. Because the vendor directory is entirely regenerated from the lock file (`salt-bundle install` re-extracts every locked package fresh), stale packages from removed dependencies are eliminated automatically on the next install run — the old subdirectory is removed by `shutil.rmtree(target_dir)` before extraction. The download cache at `~/.cache/salt-bundle/packages/` can be pruned independently; archives are content-addressed by SHA256 digest so unused files can be identified and deleted without risk of breaking current installations.
