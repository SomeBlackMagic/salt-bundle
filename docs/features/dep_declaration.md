# Dependency declaration

## gitfs

gitfs has **no dependency declaration mechanism**. There is no metadata file associated with a formula that lists other formulas it depends on. If formula A requires formula B, both must be independently configured as gitfs remotes in the Salt master config by the operator. There is no way to express this requirement in code, and there is no tooling that can read a formula repository and determine what other repositories must also be present.

## spm

spm provides **partial dependency declaration** via the `FORMULA` metadata file. This file has a `dependencies` field that lists other spm package names. However, this field is informational — spm does not automatically install declared dependencies when installing a package. The operator must manually install each dependency. The dependency list is not stored in the repository index in a structured way that tooling can act on. The format does not support version constraints for dependencies, only package names.

## salt-bundle

salt-bundle supports **full, structured dependency declaration** at two levels:

1. **Project level** (`SaltfileConfig` in `dependencies/saltfile_models.py`): `Saltfile` has a `dependencies: list[SaltfileDependency]` field. Each item declares `name`, an optional version constraint, and an optional `source` repository containing `index.yaml`.

2. **Package level** (`PackageMeta` in `packaging/models.py`): each formula's `FORMULA` has a `dependencies: list[PackageDependency]` field, where each `PackageDependency` has `name: str` and `version: str` (a semver constraint string). These package-level dependencies are read by the resolver during transitive dependency expansion. The `IndexEntry` in `dependencies/index_models.py` also stores the full dependency list so the resolver can access it without downloading the package archive.
