# Release pipeline

## gitfs

gitfs has no release pipeline concept. Releasing a new version of a formula means pushing a commit or moving a tag in the source Git repository. There is no packaging, no index update, no registry publication, and no notification mechanism. If multiple formulas live in different repositories, each must be managed independently with no orchestration layer. The Salt master will pick up changes on its next `gitfs.update` cycle, which is not triggered by the CI run itself.

## spm

spm has no automated release pipeline. After running `spm build`, the operator must manually copy the `.spm` file to the spm repository directory and run `spm create_repo <dir>` to regenerate the `SPM-METADATA` index file. There is no command to detect which formulas have new versions since the last release, no idempotency check, and no built-in support for publishing to remote storage or triggering downstream consumers. Each step must be scripted individually.

## salt-bundle

`salt-bundle repo release` implements a complete, idempotent release pipeline in a single command. The pipeline executes these steps in order: (1) initialize the provider (verify credentials or create local directories); (2) load the existing `index.yaml` to determine what has already been released; (3) discover formulas in the target directory by scanning for `.saltbundle.yaml` files; (4) skip any formula whose `name`+`version` combination already appears in the index; (5) pack each new formula to a temporary directory; (6) upload the archive via the provider's `upload_package()` method; (7) add the new entry to the in-memory `Index` object with version, URL, SHA256 digest, and metadata; (8) sort all version lists in descending semver order; (9) persist the updated `index.yaml` via `provider.save_index()`; (10) clean up the temporary directory. The command returns a list of released formulas and a list of errors, and exits with code `1` if any errors occurred.
