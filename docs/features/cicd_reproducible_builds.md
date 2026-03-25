# Reproducible builds

## gitfs

gitfs builds are not reproducible in the CI sense. Because content is pulled at runtime from a live branch, any two Salt runs separated in time may execute different code even if the CI pipeline has not changed. Pinning to a tag or a specific commit SHA mitigates this for the formula files themselves, but the act of "building" is still a runtime fetch, not a build-time snapshot. There is no lock file, no digest verification, and no way to guarantee that what was tested in CI is exactly what runs in production.

## spm

spm builds are partially reproducible. The `spm build` command reads the source directory deterministically, so the same source tree will produce the same `.spm` archive. However, there is no lock file for formula dependencies, no digest stored in the `SPM-METADATA` index, and no mechanism to verify that a downloaded `.spm` file matches a known-good hash. Reinstalling the same formula name and version from a repository gives no cryptographic guarantee that the content has not changed since the last build.

## salt-bundle

salt-bundle builds are fully reproducible. The `pack_formula()` function produces a deterministic archive from a fixed source tree: the archive name encodes `{name}-{version}`, the content is collected by `collect_files()` in a consistent order, and the archive uses `tarfile` in `w:gz` mode with no embedded timestamps that vary between runs. After packaging, `calculate_sha256()` computes a `sha256:<hex>` digest that is written into `index.yaml`. On install, `download_package()` calls `verify_digest()` which re-hashes the downloaded file and raises an error if it does not match. The `.salt-dependencies.lock` file records the resolved version, repository name, download URL, and digest for every dependency, so `salt-bundle project install` always installs exactly the same bytes regardless of what has been added to the repository since the lock was generated.
