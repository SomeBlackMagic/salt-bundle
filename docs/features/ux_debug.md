# Debug

## gitfs

Debugging gitfs problems is difficult because the failure surface spans multiple layers: Git authentication (SSH keys, tokens), network reachability, the master's gitfs cache directory, cache staleness, and Salt's fileserver request routing. When a state is missing or stale, the operator must check `salt-run fileserver.file_list saltenv=base`, inspect the gitfs cache under `/var/cache/salt/master/gitfs/`, and look at master logs with `log_level: debug`. There is no single command that shows which commit is currently active per remote. Diagnosing why a minion sees an old version often requires clearing the cache and forcing a resync.

## spm

SPM debug is also opaque. The SPM database is stored in `/var/cache/salt/spm/` as a sqlite-like structure; there is no built-in command to dump the full installed state in a human-readable way. If a module installed via SPM is not visible to Salt, the operator must check the `extmods` directory, verify `spm_logfile`, and manually cross-reference with `salt-call sys.list_modules`. Version mismatches between what SPM reports as installed and what is actually on disk are hard to detect without manual file inspection.

## salt-bundle

salt-bundle is comparatively easier to debug because the state is fully visible on the filesystem. The vendor directory (`vendor/` by default) contains one subdirectory per installed formula, each with its own `.saltbundle.yaml`. The lock file `.salt-dependencies.lock` is a plain YAML file showing the exact resolved version, repository, URL, and digest for every dependency. The loader plugin (`ext/loader.py`) emits debug log lines via Python's standard logging when it discovers formula paths, for example: `SaltBundle: loaded _modules from formulas: nginx, mysql (modules: nginx_status, mysql_query)`. If a module is not loading, the operator can verify the path by running `salt-call --local saltbundle.loader_paths` or inspecting loader debug output.
