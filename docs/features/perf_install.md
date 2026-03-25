# Install overhead

## gitfs

gitfs has no install step in the traditional sense. There is no command to run, no archive to unpack, and no package database to update. The "installation" is the initial clone of the remote repository into the gitfs cache, which happens automatically on first access. Subsequently, the Salt master serves files directly from the git object store without any additional unpacking step. This means there is effectively zero install overhead per formula beyond the initial clone cost.

## spm

spm has moderate install overhead. `spm install <package>` performs the following steps: downloads the `.spm` archive from the repository, reads the `FORMULA` metadata to determine the target paths, extracts files to the configured locations (typically `/srv/salt/formulas/<name>/` for states and `/var/cache/salt/master/extmods/` for modules), and updates the local spm package database. For modules, a subsequent `salt '*' saltutil.sync_all` is required to distribute the modules to minions, which adds network overhead proportional to the number of managed nodes.

## salt-bundle

salt-bundle has moderate but controlled install overhead. `salt-bundle project install` reads each entry from `.salt-dependencies.lock`, downloads the corresponding `.tgz` archive via HTTP (or skips download for `path`-type entries), verifies the SHA256 digest, and extracts the archive to `vendor/{package_name}/` using `unpack_formula()`. The extraction includes a path-traversal security check (rejecting any member whose name starts with `/` or contains `..`). After all packages are installed, the command attempts `salt-call --local saltutil.sync_all` to synchronize Salt extensions. Install time scales linearly with the number of dependencies and their archive sizes; there is no dependency graph traversal at install time since the lock file already contains the resolved flat list.
