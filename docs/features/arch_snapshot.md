# State Snapshot

## gitfs

gitfs does **not** provide deployment snapshots. The "state" of the formulas served by the master at any given moment is the current HEAD of the tracked Git branch at the most recent fetch. There is no explicit snapshot object, no artifact, and no manifest that captures what was deployed when. To reconstruct the state at a past point in time, one would need to examine the Git history of every tracked remote — assuming those remotes still exist and the history has not been rewritten.

## spm

spm does **not** support deployment snapshots. The spm state database (`/var/cache/salt/spm`) records which packages are installed, but does not capture when they were installed, from which repository version, or what the package contents looked like. If a package is upgraded or removed, there is no automatic record of the previous state. Creating a snapshot requires external mechanisms such as filesystem snapshots or manual tracking of installed package lists.

## salt-bundle

salt-bundle **provides full deployment snapshots** through `Saltfile.lock` and the vendor directory. The lock file records every installed package's exact resolved version, repository URL, archive URL, type, and SHA256 digest. Commit it to version control to make each deployment state addressable by a Git commit. To reproduce a past deployment, check out that commit and run `salt-bundle project install`; it reads the lock without re-running resolution. The canonical models are `LockFile` and `LockedDependency` in `dependencies/lock_models.py`.
