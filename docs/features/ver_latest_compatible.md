# Latest compatible

## gitfs

gitfs has **no concept of "latest compatible"**. Because versioning is based on Git refs rather than semver, there is no mechanism to automatically select the highest version that satisfies a given constraint from a set of candidates. The operator must manually determine the latest suitable tag or branch and configure it in the Salt master. There is no tooling to query "what is the latest 1.x release in this repository".

## spm

spm does **not support latest-compatible selection**. When `spm install formula` is run without a version argument, it installs the latest version listed in the repository index (sorted by the `version` string), but this selection is not constraint-aware — it does not respect declared dependencies or compatibility requirements. There is no "give me the latest version compatible with >=1.0,<2.0" capability.

## salt-bundle

salt-bundle implements **automatic latest-compatible selection** as the core of its resolution algorithm in `resolver.py`. The `resolve_version(constraint, candidates)` function filters all `IndexEntry` objects from the repository index against the constraint using `matches_constraint()`, then sorts the matching entries by parsed semver in descending order using `semver.Version` comparison, and returns the highest matching version. This means a constraint like `"^1.0.0"` will always resolve to the newest published `1.x.y` release automatically, without any manual intervention. This selection is performed at `salt-bundle project update` time; the result is frozen into `.salt-dependencies.lock` so that subsequent installs use the exact resolved version rather than re-running the selection.
