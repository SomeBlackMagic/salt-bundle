# No lock file

## gitfs

gitfs has no lock mechanism. The "version" of a formula is whatever commit is at the tip of the configured branch at the time Salt's gitfs cache refreshes. Even if a tag is used instead of a branch, nothing prevents the tag from being moved on the remote. There is no file checked into the Salt project that records the exact Git SHA that was used in a given deployment, making it impossible to reproduce a past environment or audit what code was running at a specific point in time.

## spm

SPM has no lock file. When `spm install` is run, it fetches the latest matching package from the repository index at that moment and installs it. The SPM database records what is currently installed, but this record lives on the master's local filesystem and is not version-controlled or shareable. Running the same `spm install` command on two different masters at two different times may produce different results if the repository index has changed between runs. There is no mechanism to commit a "resolved state" to source control.

## salt-bundle

salt-bundle generates `.salt-dependencies.lock` after every `salt-bundle project update` run. The lock file is a YAML document (defined by the `LockFile` Pydantic model in `models/lock_models.py`) that stores, for each dependency: the exact resolved version string, the repository name, the full download URL, and the SHA-256 digest of the `.tgz` archive. The `lockfile.save_lockfile()` function writes this atomically to disk. The lock file is intended to be committed to source control and shared across the team. On deployment, `salt-bundle project install` reads exclusively from this lock file — it never calls the resolver or queries the index — ensuring byte-for-byte reproducibility across environments.
