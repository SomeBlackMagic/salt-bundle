# Transparent Integration

## gitfs

gitfs integration is not transparent from the developer's perspective. The operator must explicitly configure `gitfs_remotes` in the master config, set `fileserver_backend` to include `gitfs`, and then trigger `salt-run fileserver.update` to populate the cache. Custom modules still require an explicit `saltutil.sync_*` call on minions before they can be used in states. The developer must understand that file paths are served from git branches, not from local directories, and must know the branch-to-environment mapping.

## spm

spm integration is not transparent. Installing a package does not automatically make its states callable — the operator must know that states are in `extmods/states/` and reference them correctly, or must manually update `file_roots`. There is no automatic discovery of installed formulas, no auto-registration of module paths, and no pillar integration. Each formula's integration requirements must be configured manually on both master and minion sides.

## salt-bundle

salt-bundle is designed for maximum transparency. Once `salt-bundle install` has populated `vendor/`, all integration happens automatically without any additional Salt configuration. The loader plugin registers module and state directories for every formula type at Salt startup. The `bundlefs` fileserver backend serves formula `.sls` files under the `formula_name/` namespace and exposes special directories (`_states/`, `_modules/`, etc.) at the root level for Salt's auto-sync. The `ext_pillar` plugin (registered as `saltbundle` in `salt_bundle/ext/pillar/saltbundle.py`) injects project metadata — `project_dir`, `vendor_dir`, formula names and paths — into every minion's pillar under the `saltbundle` key. The project config (`.salt-dependencies.yaml`) is discovered automatically by walking up from `config_dir` or CWD. No manual entries in `file_roots`, `module_dirs`, or `fileserver_backend` are required in the Salt master configuration.
