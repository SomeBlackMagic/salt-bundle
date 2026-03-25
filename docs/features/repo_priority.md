# Repo Priority

## gitfs

gitfs has **implicit priority** via ordering. There is no explicit numeric priority field, but when multiple remotes serve a file at the same path, Salt searches `gitfs_remotes` in the configured order and returns the first match. This means the order of entries in `gitfs_remotes` acts as a de-facto priority. Filtering of environments is possible via `gitfs_saltenv_whitelist` / `gitfs_saltenv_blacklist`, but there is no per-formula or per-package priority override.

## spm

spm has no priority mechanism for repositories. When a package exists in multiple configured spm repositories, spm does not guarantee which repository will be used, and there is no configuration option to express preference. The resolution order depends on implementation internals and the order in which `.repo` files are parsed. Operators must manually manage which repository contains which packages to avoid ambiguity.

## salt-bundle

salt-bundle supports explicit per-dependency repository pinning, which serves as a priority mechanism. In `.salt-dependencies.yaml`, a dependency can be specified as `repo_name/package_name: "version_constraint"` (e.g., `internal/nginx: "^2.0.0"`) to restrict resolution to a single named repository. When no repository prefix is given, all configured repositories are searched in the order they appear in the `repositories` list, and the first match satisfying the version constraint is used. The `allowed_repos` list in `~/.config/salt-bundle/config.yaml` provides a security-layer whitelist that limits which repositories are permitted at the user level. This combination of per-dependency pinning, ordered search, and optional allowlisting gives salt-bundle the most expressive priority model of the three tools.
