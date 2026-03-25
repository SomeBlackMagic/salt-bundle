# Multiple Repos

## gitfs

gitfs supports multiple repositories by listing them in the `gitfs_remotes` configuration array on the Salt master. Each entry can be a different Git remote URL, optionally with per-remote settings such as `root`, `mountpoint`, `saltenv`, `ref`, and `update_interval`. Salt merges the file trees from all configured remotes into a single virtual fileserver namespace, with earlier entries taking precedence in case of path conflicts. There is no limit on the number of remotes, but each adds clone and fetch overhead at startup and on each update cycle.

## spm

spm supports multiple repositories through separate `.repo` files in `/etc/salt/spm.repos.d/`. Each file defines one repository with a `url` pointing to the spm server and optional `username`/`password` for authentication. When searching for a package, spm queries all configured repositories. There is no priority system — if a package exists in multiple repos, the behavior depends on the order repositories are queried. Multiple repository support is functional but lacks fine-grained control.

## salt-bundle

salt-bundle supports multiple repositories through the `repositories` list in `.salt-dependencies.yaml` (project-scoped) and in `~/.config/salt-bundle/config.yaml` (user-global). Each entry is a `RepositoryConfig` object with `name`, `url`, and `type` fields. Dependencies can be pinned to a specific repository using the `repo_name/package_name` syntax in the `dependencies` map (e.g., `main/nginx: "^1.0.0"`), or resolved across all configured repositories when specified without a prefix. The `add_user_repository()` and `add_project_repository()` functions in `config.py` enforce unique names within their scope, preventing accidental duplicates. Repositories of different types (`remote` and `path`) can be mixed in the same configuration.
