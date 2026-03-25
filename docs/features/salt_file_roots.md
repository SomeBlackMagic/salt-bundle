# file_roots

## gitfs

gitfs does not use `file_roots` at all — it is an alternative to `file_roots`, not a supplement. When `gitfs` is listed in `fileserver_backend`, Salt resolves file requests against configured git remotes instead of (or in addition to) the local directories in `file_roots`. The two can coexist in `fileserver_backend: [roots, gitfs]`, where `roots` handles local paths and `gitfs` handles git-backed paths, with priority determined by list order.

## spm

spm does not automatically modify `file_roots`. After installation, spm places states into `extmods/states/` but this path is not added to `file_roots` by default. Operators must manually add the extmods states path to `file_roots` in the master configuration if they want to reference spm-installed states by path. This is a common source of confusion and a reason spm is considered difficult to integrate transparently.

## salt-bundle

salt-bundle explicitly avoids modifying `file_roots` for vendor content. The `configure()` function in `ext/loader.py` returns opts unchanged, with a comment explaining the deliberate design: adding `vendor/` to `file_roots` causes Salt to recursively sync `_modules` and `_states` directories into the minion cache, producing infinite nesting (`modules/modules/modules/...`). Instead, module and state loading is handled via the `module_dirs()` and `states_dirs()` loader hooks, which inject `vendor/<formula>/_modules/` and `vendor/<formula>/_states/` paths directly into Salt's loader search path. File serving for `.sls` templates is handled by the `bundlefs` fileserver backend. This separation avoids the `file_roots` anti-pattern entirely.
