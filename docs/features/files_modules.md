# Modules (_modules)

## gitfs

gitfs can serve files from `_modules/` directories in a Git repository through the fileserver, but this is only the file-delivery half of the problem. For Salt to actually load and execute custom execution modules, the master must sync them to minions via `saltutil.sync_modules` or `state.highstate` (which triggers auto-sync). The modules land in the minion's `extmods` directory (typically `/var/cache/salt/minion/extmods/modules/`). gitfs does not provide any special loader hooks — module loading goes through the standard Salt sync mechanism.

## spm

spm installs formula packages that may include `_modules/` directories. After installation, these directories are placed under the path configured in `extension_modules` (typically `/var/cache/salt/minion/extmods/`). Salt must still sync the modules to minions explicitly using `saltutil.sync_modules`. The modules become available on minions only after this sync step, which may require an additional round-trip. spm itself does not integrate with Salt's loader system; it relies entirely on the standard extmods mechanism.

## salt-bundle

salt-bundle provides a direct loader plugin integration that bypasses the extmods sync mechanism entirely. The `ext/loader.py` module implements the `module_dirs()` entry point, which Salt's loader calls during initialization to discover additional module directories. For each formula in `vendor/`, the loader scans for a `_modules/` subdirectory and returns its absolute path. This means custom execution modules from vendored formulas are available immediately on startup without running `saltutil.sync_modules`. The `_get_module_dirs("modules")` function caches discovered paths using `lru_cache` to avoid repeated filesystem scans. The same pattern applies to all other module types: grains, runners, returners, engines, etc.
