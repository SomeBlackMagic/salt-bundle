# Semver Support

## gitfs

gitfs has **no semver support**. Git tags can be named with semver strings (e.g., `v1.2.3`) by convention, but gitfs has no awareness of this naming convention. Tags are treated as opaque strings. There is no ability to express "I want the latest 1.x tag" or to compare tags as ordered version numbers. Any semver-like semantics must be implemented entirely by the operator through manual configuration of the Salt master.

## spm

spm has **no semver support**. The official recommended version format is `YYYYMM` (e.g., `201506` for June 2015), which is date-based, not semver. The `release` field is used for multiple packages within the same month. While nothing prevents an operator from writing a semver-like string in the `version` field, spm has no semver parsing library and performs no semantic version comparisons — there is no support for constraint expressions like `^1.0` or `>=1.2,<2.0`. Version matching is string-equality only.

## salt-bundle

salt-bundle has **full semver support**. Package versions are validated with a complete semver regex at build time (`validate_semver()` in `package.py`). At resolution time, `resolver.py` uses `semver.Version.parse()` from the `semver` Python library for parsing and ordering. The `resolve_version()` function sorts matching candidates by parsed semver in descending order and returns the highest match — ensuring that "latest compatible" semantics are correct even with pre-release versions (which sort below the corresponding release per semver spec). Semver pre-release and build metadata components are fully preserved in the version string stored in `IndexEntry.version` and `LockedDependency.version`.
