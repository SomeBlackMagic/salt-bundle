# Fileserver Backend

## gitfs

gitfs is itself a Salt fileserver backend — it is the canonical example of how to extend Salt's file serving layer. It is registered as `gitfs` and activated by adding `gitfs` to `fileserver_backend` in the Salt master configuration alongside `roots`. When active, Salt serves `.sls` files, templates, and static files directly from Git branches/tags, with each branch exposed as a Salt environment. The backend implements the full fileserver interface: `envs()`, `find_file()`, `file_list()`, `file_hash()`, `serve_file()`, and `update()`.

## spm

spm does not implement or register a fileserver backend. Installed formula states are placed into `extmods/` but are not served through Salt's fileserver protocol. States are accessed by Salt only when the `extmods` path is included in `file_roots` manually by the operator. This means spm-installed formulas are not visible to `salt-cp`, `cp.get_file`, or any fileserver-aware operation unless additional manual configuration is applied.

## salt-bundle

salt-bundle ships a custom fileserver backend named `bundlefs`, implemented in `salt_bundle/ext/fileserver/bundlefs.py`. It implements the complete Salt fileserver interface: `envs()` returns `['base']`; `find_file()` resolves paths in two formats — `formula_name/file.sls` for regular files and `_states/module.py` for special Salt module directories; `file_list()` exposes all vendor formula files with correct path prefixes; `file_hash()` computes SHA256 (or the hash type configured in Salt opts) for cache validation; `serve_file()` streams file content in chunks matching `file_buffer_size` from opts. The backend is automatically registered via the `fileserver_dirs()` hook in `ext/loader.py`, which appends the `salt_bundle/ext/fileserver/` directory to Salt's fileserver search path without any manual master configuration.
