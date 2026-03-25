# Version constraints (in the context of dependencies)

## gitfs

gitfs has **no version constraints on dependencies**. Because gitfs has no dependency system, the concept of a version constraint on a dependency does not apply. Each Git remote is configured to track a specific ref independently, and there is no mechanism to express or enforce compatibility between the formula versions served from different remotes.

## spm

spm has **no version constraints on dependencies**. The `FORMULA` file's `dependencies` field lists only package names, with no version range syntax. When (or if) spm were to resolve these declarations, it would have no basis for selecting a version — there is no version constraint DSL, no semver comparison, and no way for a package to say "I need formula B at version >=2.0 but less than 3.0".

## salt-bundle

salt-bundle supports **full version constraints on dependencies** at both the project and package levels. In `.salt-dependencies.yaml`, each dependency value is a version constraint string. In `.saltbundle.yaml`, each `PackageDependency.version` field is also a constraint string. These are evaluated by `resolver.matches_constraint()` during resolution.

Constraints supported (as documented in `resolver.py`):

| Syntax | Semantics |
|---|---|
| `"1.2.3"` | Exact version match |
| `"^1.2.3"` | Same major (or minor if major=0), >= base |
| `"~1.2.3"` | Same major.minor, >= base |
| `"1.2.x"` / `"1.2.*"` | Any patch under 1.2 |
| `">=1.0.0,<2.0.0"` | Comma-separated compound range |
| `">=1.0.0"` | Single comparison operator |

Transitive dependency constraints are read directly from `IndexEntry.dependencies` in the repository index, so the resolver does not need to download and unpack the package to evaluate its dependency constraints.
