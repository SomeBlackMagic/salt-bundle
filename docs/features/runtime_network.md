# Runtime Network Dependency

## gitfs

gitfs has a hard runtime dependency on the network. Every time the Salt master's gitfs poller runs (controlled by `gitfs_update_interval`, default 60 seconds), it executes `git fetch` against every configured remote. If the remote is unreachable — due to network partition, DNS failure, repository unavailability, or authentication expiry — the master cannot refresh formula content. Existing cached content continues to be served from the local git object store, but new commits, new branches, and new tags become invisible until connectivity is restored. There is no built-in circuit-breaker or degradation mode; the master simply retries on the next polling cycle.

## spm

spm has no runtime network dependency. Packages are installed to the master's `extmods` directory (typically `/var/cache/salt/master/extmods/` or `/srv/salt/_modules/`, depending on configuration) before any Salt run begins. Once installed, Salt reads formula files directly from the local filesystem. The spm repository is only contacted during `spm install` or `spm update` operations, which are administrative commands run outside of normal Salt execution. A Salt highstate can complete successfully with no network access as long as the required formulas are already installed.

## salt-bundle

salt-bundle has no runtime network dependency. All formula files are extracted to the `vendor/` directory during `salt-bundle project install`, which is an explicit administrative step. During Salt execution, the `bundlefs` fileserver backend (`ext/fileserver/bundlefs.py`) reads files directly from subdirectories under `vendor/` — it iterates the local filesystem, has no HTTP client, and makes no outbound connections. The `update()` function in bundlefs merely clears the in-process `_CACHE['vendor_roots']` list to force a re-scan of the local `vendor/` directory on the next request.
