# Autoload

## gitfs

gitfs does not provide automatic module loading. State files are served automatically through the fileserver, but custom modules (`_modules/`, `_grains/`, `_runners/`, etc.) require explicit synchronization to minions before they can be used. The operator must trigger `saltutil.sync_all` or rely on the auto-sync that occurs at the beginning of a highstate run. There is no hook mechanism that informs Salt's loader of additional module directories from gitfs sources.

## spm

spm does not provide automatic module loading. After package installation, custom modules exist as files on the filesystem, but Salt's loader is not notified of their location automatically. The operator must ensure the module directory is in the configured `extension_modules` path and trigger synchronization manually. Some spm formulas may include reactor or orchestrate states that automate this step, but this is not a built-in spm capability.

## salt-bundle

salt-bundle implements full automatic module loading through Salt's loader extension plugin system. The `ext/loader.py` module exports named functions (`module_dirs`, `states_dirs`, `grains_dirs`, `runner_dirs`, `returner_dirs`, `engine_dirs`, `beacon_dirs`, and 20+ others) that correspond to Salt's internal loader hook names. Salt calls these functions during loader initialization to discover additional search paths. The entire `vendor/` tree is scanned automatically by `_get_formula_paths()`, which iterates `vendor/` subdirectories (following symlinks for path-type repositories) and returns all valid formula paths. Results are cached using `lru_cache` and an mtime-based cache keyed on `.salt-dependencies.yaml`, so repeated calls are cheap.
