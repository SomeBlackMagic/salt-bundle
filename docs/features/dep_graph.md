# Dependency graph

## gitfs

gitfs has **no dependency graph**. Formulas served via gitfs exist as independent repositories with no declared relationships between them. There is no tooling that can produce a graph of formula dependencies because no machine-readable dependency metadata exists.

## spm

spm has **no dependency graph**. Even though `FORMULA` files can list dependency names, spm does not construct a graph from this data. There is no command to display, analyze, or traverse the dependency graph, and no internal data structure that represents it. The dependency information in `FORMULA` files is effectively unused by the tool.

## salt-bundle

salt-bundle builds and traverses a **dependency graph implicitly** during the `update` command, but does not materialize it as a named data structure. The graph is traversed via the BFS-like `pending` queue in `cli/project/update.py`: direct dependencies are added first, and each resolved package's `IndexEntry.dependencies` are appended to the queue, causing transitive dependencies to be resolved in breadth-first order. The resulting flattened dependency set is recorded in `.salt-dependencies.lock` as a flat map, without preserving the graph structure (which package required which other package). There is currently no `salt-bundle graph` or `salt-bundle show` command that would render the full dependency graph with edges. The comparison table marks this capability as partial (⚠️) because the graph is computed but not exposed to the user.
