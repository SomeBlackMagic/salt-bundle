# CI-friendly

## gitfs

gitfs has no CI-friendly characteristics in the traditional sense: it is a runtime fileserver backend configured on the Salt master, not a build-time tool. There is no artifact to produce, no pipeline step to add, and no output to cache between runs. In a CI environment you would need to reconfigure the Salt master's `gitfs_remotes` list and restart or refresh the master — operations that are inherently environment-specific and stateful. Because the content is pulled at runtime from a live Git remote, the CI job itself cannot validate what code will actually execute on the target; it can only test whether the remote repository is reachable. This makes gitfs fundamentally incompatible with the idea of a self-contained, reproducible CI pipeline.

## spm

spm has a partial CI story: the `spm build` command can be run as a pipeline step to produce a `.spm` package file, so there is at least a discrete build action. However, there is no official tooling for publishing to an spm repository from CI, no index update automation, and no built-in duplicate-version detection. The build step must be scripted manually (invoking `spm build <formula-dir>`), and the resulting artifact must be moved to the repository directory by hand. There is no `--dry-run` mode and no structured exit codes beyond generic success/failure, making it difficult to integrate cleanly into automated pipelines.

## salt-bundle

salt-bundle is designed from the ground up for CI integration. The `salt-bundle repo release` command implements a complete automated release workflow: it discovers formulas in a directory, checks the existing index to skip already-released versions, packages each new formula into a `.tgz` archive via `pack_formula()`, uploads it via the configured provider, calculates a SHA256 digest, and updates `index.yaml` — all in one idempotent operation. A `--dry-run` flag prints what would happen without making any changes, and the command exits with code `1` on any error, making it safe to use as a gate in CI pipelines. The `--skip-packaging` flag allows reusing pre-built archives in multi-stage pipelines.
