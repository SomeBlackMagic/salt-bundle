# Loader Plugin

## gitfs

gitfs does not use Salt's loader plugin system. Custom modules from git-backed formulas must be synced explicitly to minions using `salt '*' saltutil.sync_all` or `salt '*' saltutil.sync_modules` before they can be used in states. The sync operation copies module files from the gitfs-served `_modules/`, `_states/`, etc. directories into the minion's local module cache. There is no automatic hook that injects paths into Salt's loader without a sync step.

## spm

spm does not register a loader plugin. After installation, module files in `extmods/modules/` are picked up by Salt's loader only because `extmods` is on Salt's built-in module search path. This works for execution modules but still requires `saltutil.sync_*` for minion-side state modules. There is no programmatic hook that spm registers with Salt's plugin system to advertise module directories.

## salt-bundle

salt-bundle registers a comprehensive loader plugin via Python entry points. The module `salt_bundle.ext.loader` is declared as a `salt.loader` entry point, which Salt discovers at startup. This module exposes one function per Salt module type: `module_dirs()`, `states_dirs()`, `grains_dirs()`, `returner_dirs()`, `runner_dirs()`, `pillar_dirs()`, `engines_dirs()`, `proxy_dirs()`, `beacons_dirs()`, `render_dirs()`, `utils_dirs()`, `fileserver_dirs()`, and over a dozen others — covering every extensible subsystem in Salt. Each function scans the vendor directory for formula subdirectories matching `_<type>/` and returns their absolute paths. Results are cached with `functools.lru_cache` keyed by formula type. The `fileserver_dirs()` hook additionally injects the `bundlefs` backend from inside the `salt_bundle` package itself. No manual Salt configuration is required beyond listing `salt_bundle` in the entry point registry.
