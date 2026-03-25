# No transitive deps

## gitfs

gitfs does not support transitive dependencies at all. Each formula repository is added independently to `gitfs_remotes`. If formula A depends on formula B, and formula B depends on formula C, the operator must manually configure all three remotes. There is no graph traversal, no automatic discovery of indirect dependencies, and no mechanism for a formula to declare what other formulas it requires at the Git level.

## spm

SPM does not support transitive dependency resolution. Even though the `FORMULA` file allows listing dependencies by name, SPM never follows the dependency chain of an installed package to discover its own dependencies. The operator is responsible for manually identifying and installing the full transitive closure. In practice, most SPM packages either declare no dependencies or declare them only as documentation, not as an actionable instruction to the package manager.

## salt-bundle

salt-bundle resolves transitive dependencies recursively, but conflict resolution is absent. In `cli/project/update.py`, the resolution loop processes a `pending` list that starts with the direct dependencies declared in `.salt-dependencies.yaml`. When a package is resolved to a specific `IndexEntry`, its `dependencies` list (from the repository index entry) is appended to `pending` as additional `(name, version_constraint)` tuples. The loop continues until `pending` is empty, meaning it walks the full dependency graph. However, if two different packages in the graph require the same transitive dependency with incompatible version constraints, the current implementation takes whichever version it resolves first (`if pkg_name in resolved_packages: continue` — the TODO comment in the code explicitly notes that version compatibility is not checked). This means conflicting transitive dependencies are silently ignored in favor of the first-resolved version.
