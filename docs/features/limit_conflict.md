# No conflict resolution

## gitfs

Conflict resolution is not applicable to gitfs in any meaningful sense. Since gitfs has no dependency system and no concept of versions beyond branch/tag names, there is nothing to conflict. If two formulas both provide a file at the same path, the last `gitfs_remotes` entry wins according to Salt's fileserver priority rules. There is no diagnostic tooling to detect or warn about such overlaps.

## spm

SPM has no conflict resolution. If two SPM packages install files with the same name into `extmods/`, the second install silently overwrites the first. There is no version constraint syntax in SPM's dependency declarations, so the concept of "which version satisfies both A and B" is never evaluated. The SPM database will reflect the last-installed state but will not report the overwrite or flag it as a conflict.

## salt-bundle

salt-bundle currently has no conflict resolution algorithm. When the transitive dependency resolver in `cli/project/update.py` encounters a package name that has already been placed in `resolved_packages`, it skips it entirely with a `continue` statement and a `# TODO: Check version compatibility` comment. This means: if package A requires `common >= 1.0.0` and package B requires `common >= 2.0.0`, and A's dependency is resolved first, the `2.0.0` constraint from B is silently ignored and `common 1.x` is used. No error is raised, no warning is printed, and the lock file records only the first-resolved version. Implementing proper conflict detection (e.g., collecting all constraints for a given name and checking their intersection before selecting a version) is a known gap in the current implementation.
