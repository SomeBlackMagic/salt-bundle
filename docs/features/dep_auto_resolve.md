# Automatic Resolution

## gitfs

gitfs provides **no automatic dependency resolution**. There is no resolution step at all — the operator configures each formula repository manually in the Salt master config. If formula B is a dependency of formula A, the operator must know this and add B as a separate gitfs remote. If B in turn depends on C, the operator must also add C. Discovery and configuration are entirely manual and implicit, based on documentation or tribal knowledge rather than machine-readable metadata.

## spm

spm has **partial automatic dependency resolution**. The `FORMULA` file supports a `dependencies` field (comma-separated package names), and the official Salt documentation states that "SPM attempts to discover and install dependencies automatically." In practice, however, this mechanism is rudimentary: there are no version constraints, no conflict detection, and no transitive resolution. If a required dependency is not available in the configured repositories, spm will fail without a useful error. The resolution is name-based only — it finds a package by name and installs it, with no guarantee of compatibility.

## salt-bundle

salt-bundle implements **fully automatic dependency resolution** in the `update` command (`cli/project/update.py`). The resolution algorithm works as follows:

1. A `pending` list is initialized from the `dependencies` in `.salt-dependencies.yaml`.
2. All configured repository indexes are pre-fetched (via `repository.fetch_index()` or `repository.fetch_index_from_path_repo()`).
3. For each item in `pending`, `parse_dependency_name()` splits the key into an optional repository name and a package name. If a repository is specified, only that repository is searched; otherwise all repositories are tried in order.
4. `resolver.resolve_version(constraint, candidates)` selects the best matching `IndexEntry` from the repository index.
5. The resolved `IndexEntry.dependencies` list is appended to `pending`, driving transitive resolution.
6. Resolved packages are recorded in a `LockFile` object and written to disk.
7. All resolved packages are then downloaded (with digest verification) and installed to the vendor directory.

The entire process exits with a non-zero code if any dependency in the pending queue cannot be resolved.
