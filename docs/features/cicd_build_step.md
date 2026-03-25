# Build step

## gitfs

gitfs has no build step. Formula content is served directly from the Git repository at runtime; there is nothing to compile, package, or archive. The "build" in a gitfs workflow is simply a `git push` to the source repository, after which the Salt master's gitfs poller fetches the new commit on its next update cycle. This means there is no discrete, auditable artifact produced by the CI pipeline — the pipeline output is the state of a remote branch or tag.

## spm

spm has an explicit build step: `spm build <formula-dir>` reads the `FORMULA` metadata file and creates a `.spm` package archive. This step must be added manually to the CI pipeline script. The `FORMULA` file must declare `name`, `version`, `os`, `os_family`, and `dependencies`. The build step validates that these fields are present and that the formula directory contains valid state files, but it does not enforce semver format or validate dependency version constraints. The resulting `.spm` file is a binary archive (using Python's `tarfile` module) suitable for distribution.

## salt-bundle

salt-bundle provides `salt-bundle formula pack` as the dedicated build step. Internally it calls `pack_formula()` in `package.py`, which: loads `.saltbundle.yaml` metadata, validates the package name against the pattern `^[a-z0-9_-]+$`, validates the version against a full semver regex (including pre-release and build metadata suffixes), checks that at least one `.sls` file exists, collects all formula files via `collect_files()`, and writes a `tar.gz` archive named `{name}-{version}.tgz`. The build step is deterministic: given the same source tree and metadata, it always produces the same archive layout. It can be combined with `--output-dir` to write the artifact to a CI workspace directory, and with `--skip-packaging` in the release command to reuse a pre-built archive in a subsequent stage.
