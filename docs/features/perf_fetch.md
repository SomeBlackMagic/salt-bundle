# Fetch overhead

## gitfs

gitfs incurs continuous fetch overhead throughout its operational lifetime. On every update cycle (default: every 60 seconds), the Salt master executes `git fetch` for every configured remote. Each fetch involves a TCP connection, SSH or HTTPS handshake, and a Git smart-protocol negotiation, even when no new commits are available. With many gitfs remotes (one per formula is a common pattern), this overhead accumulates. The master's background `gitfs.update` thread blocks until all fetches complete, which can add latency to state rendering if a remote is slow. Under high load or poor network conditions, fetch timeouts can cascade and delay state delivery to minions.

## spm

spm has no periodic fetch overhead. The spm repository index (`SPM-METADATA`) is only downloaded when the operator explicitly runs `spm update`. Between updates, spm reads package information from a local cache. There is no background polling process, no network activity during Salt execution, and no connection to the spm repository during a highstate run.

## salt-bundle

salt-bundle has no fetch overhead at runtime. The `bundlefs` fileserver backend reads files entirely from the local `vendor/` directory and makes no network calls. Fetching — in the sense of downloading a package archive — only happens during `salt-bundle project install` or `salt-bundle project update`, which are explicit administrative commands. The `index.yaml` is fetched once per `update` invocation and is not re-downloaded during Salt execution. For the GitHub provider, `load_index()` uses `git fetch origin gh-pages` followed by `git show gh-pages:index.yaml`, which is a single network round-trip per release operation, not a continuous background process.
