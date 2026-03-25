# Module Location

## gitfs

With gitfs, custom modules reside in the gitfs cache on the Salt master, typically under `/var/cache/salt/master/gitfs/<hash>/`. After a `saltutil.sync_modules` call, copies of these modules are placed on each minion under `/var/cache/salt/minion/extmods/modules/`. The minion executes modules from the `extmods` location. The gitfs cache is managed automatically by the Salt master; each configured remote gets its own cache directory identified by a hash of the remote URL and branch.

## spm

spm installs formula files into a path configured in Salt's `file_roots` (typically `/srv/spm/salt/`). Custom modules within those formulas are installed alongside state files in the same directory tree, for example `/srv/spm/salt/formula_name/_modules/`. After `saltutil.sync_modules`, minions receive copies in their `extmods` directory (`/var/cache/salt/minion/extmods/modules/`). The exact location of spm-installed files depends on the `spm_formula_path` and related configuration options in the Salt master config.

## salt-bundle

salt-bundle stores modules inside the project's `vendor/` directory (configurable via `vendor_dir` in `.salt-dependencies.yaml`, defaulting to `"vendor"`). Each formula is unpacked as a subdirectory, so modules for a formula named `nginx-formula` are at `vendor/nginx-formula/_modules/`. The `_get_formula_paths()` function in `ext/loader.py` scans `vendor/` and returns paths to each formula directory. The `_get_module_dirs(formula_type)` function then constructs paths like `vendor/nginx-formula/_modules` and returns them to Salt's loader. Modules are read directly from `vendor/` at runtime — no copy to a separate extmods location is made.
