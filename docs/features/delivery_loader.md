# Loader Integration

## gitfs

gitfs integrates with Salt's loader through the standard fileserver backend mechanism. It implements the `__virtual__`, `envs`, `find_file`, `file_list`, `dir_list`, `file_hash`, and `serve_file` functions that Salt's fileserver subsystem calls. This is a fileserver-level integration only — gitfs does not participate in Salt's module loader subsystem. Module loading from gitfs-served paths still requires the standard `saltutil.sync_*` flow, which copies files through the fileserver into the minion's extmods cache before the loader picks them up.

## spm

spm has no custom loader integration. Installed packages are placed in directories that must be manually added to the standard Salt configuration (`file_roots`, `extension_modules`). The Salt loader then uses its built-in directory scanning logic to find modules in those configured paths. spm is a package installer, not a loader plugin — it does not register itself with Salt's extension mechanism.

## salt-bundle

salt-bundle implements a full plugin-based loader integration via Salt's `*_dirs` hook protocol. The `ext/loader.py` module is registered as a Salt loader extension (entry point group `salt.loader`), and Salt calls its exported `*_dirs` functions during every loader initialization. This covers all Salt module namespaces: `module_dirs`, `states_dirs`, `grains_dirs`, `runner_dirs`, `returner_dirs`, `executor_dirs`, `cache_dirs`, `log_handlers_dirs`, `matchers_dirs`, `netapi_dirs`, `pillar_dirs`, `queue_dirs`, `roster_dirs`, `sdb_dirs`, `serializers_dirs`, `outputter_dirs`, `beacons_dirs`, `engines_dirs`, `proxy_dirs`, `cloud_dirs`, `thorium_dirs`, `tokens_dirs`, `wheel_dirs`, `render_dirs`, `wrapper_dirs`, `utils_dirs`, `top_dirs`, `pkgdb_dirs`, and `pkgfiles_dirs`. The `fileserver_dirs` function additionally injects the bundlefs backend itself by appending the `salt_bundle/ext/fileserver/` path. The `configure()` hook explicitly avoids modifying `file_roots` to prevent Salt from recursively copying `_modules`/`_states` directories into its cache.
