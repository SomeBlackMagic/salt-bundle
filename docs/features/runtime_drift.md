# Drift Possible

## gitfs

Configuration drift is a fundamental characteristic of gitfs when branch-based references are used. Because the Salt master periodically fetches from the remote and immediately serves the latest commit, two highstate runs on the same node separated by a commit to the branch may execute different formula code. Drift can occur silently: the node's state has changed not because an operator made a deliberate decision, but because a commit landed between runs. The only way to prevent drift is to pin all gitfs remotes to specific tags or commit SHAs and never use floating branch references in production.

## spm

Drift is possible but less likely than with gitfs. Once a formula is installed via spm, it does not change unless `spm install` or `spm update` is explicitly run. However, if two nodes installed the same formula at different times and the spm repository was updated between those installs, the nodes may be running different formula versions under the same name. There is no version pinning at the project level and no lock file to enforce consistency across nodes. An administrator who runs `spm update` on one node but not another introduces silent version skew.

## salt-bundle

Drift is not possible by design. The `.salt-dependencies.lock` file pins every dependency to an exact version, repository, download URL, and SHA256 digest. `salt-bundle project install` reads exclusively from the lock file — it does not re-resolve version constraints, does not consult the repository index for newer versions, and errors out immediately if the lock file does not exist. The `verify_digest()` call during download ensures that even if the artifact at the pinned URL has been replaced, installation will fail rather than silently install different content. The `vendor/` directory is a stable, fully committed snapshot; its contents change only when an operator explicitly runs `salt-bundle project update` and commits the resulting lock file changes.
