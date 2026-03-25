# State Snapshot

## gitfs

gitfs does **not** provide deployment snapshots. The "state" of the formulas served by the master at any given moment is the current HEAD of the tracked Git branch at the most recent fetch. There is no explicit snapshot object, no artifact, and no manifest that captures what was deployed when. To reconstruct the state at a past point in time, one would need to examine the Git history of every tracked remote — assuming those remotes still exist and the history has not been rewritten.

## spm

spm does **not** support deployment snapshots. The spm state database (`/var/cache/salt/spm`) records which packages are installed, but does not capture when they were installed, from which repository version, or what the package contents looked like. If a package is upgraded or removed, there is no automatic record of the previous state. Creating a snapshot requires external mechanisms such as filesystem snapshots or manual tracking of installed package lists.

## salt-bundle

salt-bundle **provides full deployment snapshots** through the combination of `.salt-dependencies.lock` and the vendor directory. The lock file records, for every installed package: exact resolved version, repository name, download URL, and SHA256 digest in the format `sha256:<hex>`. This file is designed to be committed to version control, making every deployment state permanently addressable by a Git commit. Reproducing a past deployment state requires only checking out the corresponding commit and running `salt-bundle project install`, which reads the lock file and downloads each package at its recorded digest without re-running resolution. The `LockFile` and `LockedDependency` Pydantic models in `models/lock_models.py` define the canonical schema for this snapshot.
