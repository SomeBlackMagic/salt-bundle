# Source

## gitfs

The only supported source is a **Git repository** (local bare repo or any remote accessible via `git://`, `https://`, or `ssh://`). gitfs uses the `gitpython` or `pygit2` Python library to interact with the remote. The Salt master configuration lists one or more `gitfs_remotes` entries; each remote is cloned and cached locally. Branches, tags, and commits are the only addressing mechanisms — there is no separate versioning layer on top of Git's own ref system. Files from different remotes can be merged using `saltenv` mappings (e.g., `base` → `main` branch, `prod` → `production` branch).

## spm

The source for spm packages is **`.spm` archive files** hosted in an spm repository. An spm repository is a directory (served over HTTP or stored locally) that contains `.spm` packages and a generated `SPM-METADATA` index file. The `.spm` format is a tar archive containing formula files plus a `FORMULA` metadata file. Repository URLs are configured in `/etc/salt/spm.d/` or the main `spm.conf`. Multiple repository sources can be configured but there is no priority ordering or source pinning per dependency.

## salt-bundle

The source for salt-bundle packages is **`.tgz` (gzipped tar) archives**. Archives are hosted in repositories that serve an `index.yaml` file (an `Index` Pydantic model with `apiVersion`, `generated`, and a `packages` map). Repositories can be HTTP/HTTPS URLs, `file://` paths, or local directories (`type: path` in `RepositoryConfig`). For `type: path` repositories, salt-bundle reads `.saltbundle.yaml` directly from the formula directory and synthesises an in-memory index entry with `digest: "path"` — no archive is created; instead, the directory is symlinked into `vendor/`. The `index.yaml` stores, per package version, the URL, SHA256 digest, and the full dependency list extracted from `.saltbundle.yaml`.
