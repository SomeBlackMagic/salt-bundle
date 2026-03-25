# Sync Required

## gitfs

gitfs always requires a sync step to deliver modules (execution modules, grains, runners, etc.) to minions. After gitfs serves `_modules/` files through the fileserver, those files must be explicitly synced via `saltutil.sync_modules`, `saltutil.sync_all`, or the implicit sync that occurs at the start of `state.highstate`. Until sync is complete, new or updated modules from the repository are not executable on the minion. State files (`.sls`) themselves do not need syncing — they are rendered on the master and executed via the standard job system.

## spm

spm has a partial sync requirement. After installing an spm package on the master, any custom modules included in the package must be synced to minions using `saltutil.sync_modules` or `saltutil.sync_all` before they become available for execution. If spm is used to install packages directly on minions (not just the master), the sync step may be skipped for modules installed locally, but this is an atypical deployment pattern. State files become available without sync once the install directory is in `file_roots`.

## salt-bundle

salt-bundle requires no sync step for module delivery. The `ext/loader.py` plugin implements Salt's loader extension hooks (`module_dirs()`, `states_dirs()`, `grains_dirs()`, etc.), which are called by Salt's internal loader during startup and module reloading. These hooks return the absolute filesystem paths to `_modules/`, `_states/`, `_grains/`, and all other module type directories found inside `vendor/` formulas. Because the loader reads modules directly from `vendor/` at load time, there is no intermediate sync or copy step — the modules are available immediately on the next Salt process start or `saltutil.refresh_modules`.
