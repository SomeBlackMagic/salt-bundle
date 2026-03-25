# Scalability

## gitfs

gitfs scales moderately at the master level but has well-known bottlenecks at scale. The main scalability constraint is the periodic `git fetch` loop: with N formula repositories, the master performs N network round-trips every `gitfs_update_interval` seconds. This is a single-threaded operation per remote by default, so a slow or unresponsive remote blocks the update of all subsequent remotes in the list. At the minion level, all file requests flow through the master's gitfs cache, making the master a central bottleneck. Horizontal scaling (multiple masters) requires either shared gitfs cache storage or accepting that each master maintains its own independent git clones.

## spm

spm scales well at runtime because there is no shared runtime state between the package manager and Salt execution. Once packages are installed on the master (and modules synced to minions via `saltutil.sync_all`), scaling to additional minions is a matter of Salt's standard ZeroMQ/transport layer, not spm's concern. The spm repository is a passive HTTP server that is only contacted during administrative installs, so it can be a simple static file host (Nginx, S3, GitHub Pages) with no dynamic components. The main scalability limitation is that there is no built-in mechanism to ensure that all masters in a multi-master setup have the same formula versions installed.

## salt-bundle

salt-bundle scales well at both the formula distribution and runtime levels. At distribution time, the repository is a static HTTP server serving `index.yaml` and `.tgz` archives — it can be a CDN, S3 bucket, or GitHub Pages, all of which handle arbitrary request volumes without server-side logic. At runtime, the `bundlefs` backend reads from local disk, so its performance scales with the master's filesystem I/O capacity rather than any network resource. In a multi-master setup, each master runs `salt-bundle project install` independently from the same lock file, guaranteeing identical `vendor/` contents without requiring shared storage. The `index.yaml` structure (a dictionary of package names to sorted version lists) supports thousands of packages with no performance degradation during version resolution, which uses a single linear scan over the candidate list for each dependency.
