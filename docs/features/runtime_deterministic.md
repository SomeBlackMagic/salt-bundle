# Deterministic execution

## gitfs

Execution is not deterministic when floating branch references are used. The formula code that executes during a highstate depends on the current HEAD of the configured branch at the moment the Salt master's gitfs cache was last refreshed. Two otherwise identical Salt runs may apply different state logic if a commit landed between them. Even with tag pinning, there is a window between when the tag is created and when the gitfs cache is refreshed during which the old code is still served. There is no mechanism to atomically switch all minions to a new formula version simultaneously.

## spm

Execution is partially deterministic. Once installed, spm packages do not change autonomously, so repeated highstate runs on a single node will execute the same formula code. However, determinism across multiple nodes is not guaranteed: nodes that installed the same formula at different times may have different versions. There is also no digest verification on installation, so content-level integrity is not enforced — a repository maintainer could replace an artifact at the same version string without detection.

## salt-bundle

Execution is fully deterministic. Every dependency in `.salt-dependencies.lock` records an exact version and a `sha256:<hex>` digest. `salt-bundle project install` verifies the digest of every downloaded archive before extracting it to `vendor/`. The `bundlefs` fileserver backend serves files directly from `vendor/` subdirectories with no caching layer between the filesystem and Salt (the `_CACHE['vendor_roots']` list is only an in-process path index, not file content). Because the lock file is committed to version control alongside the Salt project, every environment that runs `git pull && salt-bundle project install` gets byte-for-byte identical formula code. Execution outcomes differ only when the managed system's state differs, not because of formula version skew.
