# Version constraints

## gitfs

gitfs supports **no version constraints**. A repository configuration references a single specific ref — there is no syntax for expressing "any tag in the 1.x series" or "the latest stable tag". The operator must manually identify the desired ref and configure it explicitly. Adding constraint evaluation would require an external script to query remote tags and update the Salt master config.

## spm

spm supports **no version constraints** in the sense of range expressions. An `spm install` command can specify an exact version, but there is no DSL for expressing `>=1.0,<2.0` or `^1.2`. The repository index does not store dependency constraints for packages, so even if constraint syntax existed at the CLI level, it could not be propagated through transitive dependencies. Version selection is always exact or implicit (latest available).

## salt-bundle

salt-bundle implements a **rich version constraint DSL** in `resolver.py`. The `matches_constraint(version, constraint)` function supports five constraint forms:

- **Exact**: `"1.2.3"` — matches only that version.
- **Caret `^`**: `"^1.2.3"` — compatible within the same major version (for `major > 0`), same minor version (for `major == 0, minor > 0`), or same patch (for `0.0.z`). Implements the npm/Cargo caret semantics.
- **Tilde `~`**: `"~1.2.3"` — compatible within the same `major.minor` range.
- **Wildcard**: `"1.2.x"` or `"1.2.*"` — matches any patch version under 1.2.
- **Range**: `">=1.0.0,<2.0.0"` — comma-separated list of comparison operators (`>=`, `<=`, `>`, `<`, `=`), all of which must be satisfied simultaneously.

Constraints are declared in `.salt-dependencies.yaml` under `dependencies` and also in each formula's `.saltbundle.yaml` `PackageDependency.version` field for transitive dependency resolution.
