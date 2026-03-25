# Storage Location

## gitfs

gitfs stores formula content in the Salt master's gitfs cache, located under `$cachedir/gitfs/` (typically `/var/cache/salt/master/gitfs/`). Each configured remote gets its own subdirectory identified by a hash of the remote URL. On every `fileserver.update` cycle, Salt calls `git fetch` against each configured remote and updates the local bare clone inside the cache. The working tree is checked out on demand per-environment (branch/tag). Files are never stored in the project directory — they exist only in the Salt master cache and are served to minions over the Salt file protocol. This means the storage location is always remote from the developer's perspective and is entirely managed by the Salt master process.

## spm

spm installs formula packages into Salt's `extension_modules` directory (`extmods`), configurable via `extension_modules` in `master` or `minion` configuration (default `/var/cache/salt/master/extmods` on the master side, `/var/cache/salt/minion/extmods` on the minion side). After `spm install <package>`, the formula's states land in `extmods/states/`, custom modules in `extmods/modules/`, etc. There is no project-local directory; installed files are mixed into the shared `extmods` tree alongside all other installed packages. The repository cache (downloaded `.spm` files before installation) lives in `/var/cache/spm/` by default.

## salt-bundle

salt-bundle extracts all formula archives into a project-local `vendor/` directory (configurable via `vendor_dir` in `.salt-dependencies.yaml`). Each formula occupies its own subdirectory: `vendor/<formula-name>/`. The presence of a `.saltbundle.yaml` file inside that subdirectory is used as the canonical marker that the formula is properly installed (`is_package_installed()` in `vendor.py` checks for this file). Downloaded `.tgz` archives are cached separately in `~/.cache/salt-bundle/packages/` (XDG-compliant, overridable via `XDG_CACHE_HOME`), keyed by the SHA256 digest of the archive (`<sha256hex>.tgz`), so identical content is never downloaded twice regardless of the package name or version.
