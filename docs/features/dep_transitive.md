# Transitive dependencies

## gitfs

gitfs has **no transitive dependency resolution**. Because there is no dependency metadata and no resolver, the concept of transitive dependencies is entirely absent. If formula A requires B, and B requires C, the operator must manually configure all three as separate gitfs remotes. There is no mechanism for B to declare that C is required, and no tooling that would discover this.

## spm

spm has **no transitive dependency resolution**. Even if package A's `FORMULA` file lists package B as a dependency, and B's `FORMULA` file lists C, spm will not automatically install B and C when A is installed. The operator must install each package manually. The transitive closure of the dependency graph is never computed.

## salt-bundle

salt-bundle resolves **transitive dependencies recursively** via the BFS loop in `cli/project/update.py`. After resolving a direct dependency, the code appends the resolved `IndexEntry.dependencies` list to the `pending` queue:

```python
for trans_dep in resolved_entry.dependencies:
    pending.append((trans_dep.name, trans_dep.version))
```

The resolver then processes these transitive dependencies in subsequent iterations, fetching them from repositories and — if they have their own dependencies — appending further items to `pending`. This continues until the queue is empty. Transitive dependencies are stored in `IndexEntry.dependencies` within the repository index (`index.yaml`), so the resolver can access them without downloading and unpacking the package archive itself. Once resolved, transitive packages appear in the lock file and vendor directory alongside direct dependencies — they are fully installed and available to Salt. The comparison table marks this as partial (⚠️) because conflict resolution between incompatible transitive constraints is not implemented: if two packages require different incompatible versions of the same transitive dependency, the last-resolved version wins silently.
