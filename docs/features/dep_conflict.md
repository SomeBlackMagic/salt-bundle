# Conflict resolution

## gitfs

gitfs has **no conflict resolution** capability. There is no dependency system, so the concept of a dependency version conflict does not arise at the tooling level. If two different gitfs remotes contain files with the same path, Salt resolves the conflict by repository priority order in the master config — the first remote in the list wins. This is a file-level collision policy, not a dependency version conflict resolution strategy.

## spm

spm has **no conflict resolution** capability. Because spm does not resolve or track inter-package dependencies, version conflicts between packages cannot be detected. If two packages install files to the same path, the later installation silently overwrites the earlier one. There is no mechanism to detect that package A requires formula B at version 1.x while package C requires formula B at version 2.x, because this relationship is not machine-readable.

## salt-bundle

salt-bundle currently has **no conflict resolution** for dependency version conflicts. This is documented as a known limitation in the comparison table and in the notes section of `salt_tools_comparison.md`. The resolution algorithm in `cli/project/update.py` uses a `resolved_packages` dict to track already-resolved packages:

```python
if pkg_name in resolved_packages:
    # TODO: Check version compatibility
    continue
```

The `# TODO` comment explicitly marks the missing conflict detection. In practice, if package A declares `nginx: "^1.0.0"` and package B declares `nginx: "^2.0.0"` as transitive dependencies, whichever is resolved first will be recorded in the lock file, and the second occurrence will be silently skipped without checking whether the already-resolved version satisfies the second constraint. This means conflicting transitive dependencies can go undetected. Implementing proper conflict resolution (e.g., backtracking, version negotiation, or explicit error reporting) remains future work.
