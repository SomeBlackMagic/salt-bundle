# No dependency system

## gitfs

gitfs has no dependency system whatsoever. Each `gitfs_remotes` entry is a flat Git URL with an optional branch/tag pin. There is no manifest file that declares what other formulas a given formula depends on, no index that maps formula names to versions, and no resolution step. If formula A requires formula B, the operator must manually add B's repository to `gitfs_remotes`. When the set of formulas grows, dependency tracking becomes entirely manual and is typically maintained only in documentation or team wikis. There is no tooling to detect missing or incompatible formula combinations.

## spm

SPM nominally supports dependency declarations via the `dependencies` field in the `FORMULA` file. However, this is purely declarative metadata — SPM does not automatically download or install declared dependencies. The operator must resolve them manually and install each package in the correct order. There is no version constraint syntax beyond a flat package name, and no index query to find which version of a dependency satisfies a requirement. In practice, the dependency field is rarely populated and even more rarely acted upon by tooling.

## salt-bundle

salt-bundle implements a full dependency system. Dependencies are declared in `.salt-dependencies.yaml` under the `dependencies` key using the format `package_name: version_constraint` (e.g., `nginx: "^1.2.0"`) or with an explicit repository qualifier (`main/mysql: "2.3.1"`). The `ProjectConfig` Pydantic model validates the structure on load. During `salt-bundle project update`, the resolver queries repository indexes, evaluates constraints via `resolver.resolve_version()`, and writes pinned results to the lock file. This makes salt-bundle the only one of the three tools that treats formula dependencies as a first-class concept with automated resolution.
