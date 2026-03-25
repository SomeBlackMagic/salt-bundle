# Repo Whitelist

## gitfs

gitfs has no repository whitelist mechanism. Any git URL listed in `gitfs_remotes` in the master configuration will be fetched unconditionally. Restricting which remotes may be configured is an administrative concern left entirely to the operator — there is no Salt-level enforcement. A misconfigured or compromised master configuration could pull from arbitrary git sources.

## spm

spm has no repository whitelist. The `spm.d/` configuration directory allows adding any number of repository entries, and `spm install` will search all of them without restriction. There is no configuration option to limit which repository URLs are trusted or to prevent installation from unlisted sources.

## salt-bundle

salt-bundle implements a repository whitelist via the `allowed_repos` field in `UserConfig` (defined in `models/config_models.py` and stored at `~/.config/salt-bundle/config.yaml`). This is a user-level list of permitted repository names or URLs. Additionally, repositories are declared explicitly in `.salt-dependencies.yaml` under `repositories`, with each entry having a `name` and `url`, and optionally a `type` (`remote` or `path`). Project dependencies can be pinned to a specific repository using the `repo_name/package_name` format in the `dependencies` map (e.g., `main/mysql: '2.3.1'`), ensuring that a package can only be resolved from the named repository even when multiple repositories are configured. This combination of a user-level allowed list and per-dependency repository pinning provides layered control over which sources are trusted at installation time.
