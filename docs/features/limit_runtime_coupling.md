# Runtime coupling

## gitfs

gitfs has the highest runtime coupling of the three tools. Every Salt run that touches a gitfs-served state depends on: network connectivity to the Git remote, Git authentication (SSH keys or tokens available on the master), the remote repository being available and returning the expected data, and the master's gitfs cache being fresh. If any of these conditions fail — the remote goes down, credentials expire, a firewall rule changes — Salt runs will fail or produce stale results. The master is tightly coupled to the Git remote at runtime, and there is no fallback mechanism.

## spm

SPM has low runtime coupling. Once packages are installed via `spm install`, the files sit in `extmods/` on the master's local filesystem. No network access is needed at Salt run time. The master is not coupled to the SPM repository at runtime; the repository is only consulted during explicit install or update operations. The only runtime dependency is the local filesystem, which is the same dependency that Salt always has.

## salt-bundle

salt-bundle has low runtime coupling, equivalent to SPM. The vendor directory is populated at deploy time (`salt-bundle project install`), and the loader plugin (`ext/loader.py`) reads from the local filesystem only — it scans the `vendor/` directory for formula subdirectories and registers their `_modules`, `_states`, and other extension paths with Salt's loader. The `_find_project_config()` function uses a cache keyed by filesystem mtime, so repeated calls within a Salt run incur no additional I/O. At Salt run time there is no network dependency, no connection to a package repository, and no Git remote — only local filesystem reads of the already-vendored formula files.
