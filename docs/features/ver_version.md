# Version

## gitfs

Versioning in gitfs is expressed through **Git refs**: branch names, tag names, or commit SHAs. The Salt master configuration maps each ref to a Salt environment (saltenv). For example, `gitfs_saltenv` can map `base` → `main`, `production` → `v2.1.0-tag`. There is no separate version number for formula content — the Git ref is the only version identifier. Multiple versions of the same formula can coexist only as separate branches or tags in the same repository, or as separate repositories. There is no version comparison, no ordering of versions beyond Git's commit graph, and no machine-readable version field in any metadata file.

## spm

spm supports **version and release** fields in the `FORMULA` metadata file, following a format borrowed from RPM packaging: `version` is a string (e.g., `2.3`), and `release` is an integer release counter within that version. spm's repository index stores these fields and allows installing a specific version with `spm install formula=2.3`. However, the version format is not validated as semver — arbitrary strings are accepted, and comparison is string-based. There is no guaranteed ordering between versions, and the `release` counter complicates comparison further. The version field is primarily informational rather than machine-enforceable.

## salt-bundle

salt-bundle uses **strict semantic versioning (semver)** as the sole version format. The `version` field in `.saltbundle.yaml` is validated against a full semver regular expression in `package.py` (`SEMVER_PATTERN`) at pack time — a package with a non-semver version string cannot be built. The `PackageMeta` model stores `version: str` with the expectation that it conforms to `MAJOR.MINOR.PATCH[-prerelease][+build]`. The `resolver.py` module uses the `semver` Python library (`semver.Version.parse`) for all version comparisons, enabling deterministic ordering and constraint evaluation. The `IndexEntry` in `index_models.py` carries the version string for each available package release.
