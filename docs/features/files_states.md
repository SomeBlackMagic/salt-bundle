# States (.sls)

## gitfs

gitfs serves `.sls` files directly from a Git repository at runtime. The Salt master clones each configured remote into its gitfs cache (typically `/var/cache/salt/master/gitfs/`) and re-fetches on every fileserver update cycle. State files are addressed by their path relative to the repository root, mapped into the Salt fileserver namespace (e.g., `salt://nginx/init.sls`). Multiple branches or tags can be mapped to separate Salt environments (`base`, `dev`, `prod`) via the `gitfs_saltenv` configuration. Because state files live in Git, every change is immediately available on the next fetch — no packaging step is required.

## spm

spm installs formula packages (`.spm` archives) onto the master or minion, placing state files into a dedicated formula directory (typically `/srv/spm/salt/` or a path added to `file_roots`). The installed states become available to the Salt fileserver through standard `file_roots` configuration. spm does not serve files itself — it simply copies them to disk at install time, and the standard Salt fileserver backend takes over from there. Updating a formula requires reinstalling the package; there is no incremental sync mechanism.

## salt-bundle

salt-bundle stores state files inside formula directories unpacked into the project's `vendor/` directory (e.g., `vendor/nginx-formula/`). The `bundlefs` fileserver backend (`salt_bundle/ext/fileserver/bundlefs.py`) discovers all subdirectories in `vendor/` and serves `.sls` files under the path `formula_name/file.sls`. The `find_file()` function maps a Salt path like `nginx-formula/init.sls` to the absolute filesystem path `vendor/nginx-formula/init.sls`. States are available immediately after `salt-bundle install` without any additional `file_roots` configuration, because bundlefs registers itself as a fileserver backend via the loader plugin.
