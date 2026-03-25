# Dev workflow

## gitfs

gitfs provides the fastest inner loop for formula development. Because states are served directly from a Git repository, a developer can push a commit (or even work from a local branch configured in `gitfs_remotes`) and trigger `salt-call state.apply` immediately. There is no build step, no packaging, no upload. The master picks up changes on the next gitfs cache refresh (configurable via `gitfs_update_interval`, default 60 seconds) or immediately after `salt-run fileserver.update`. This makes gitfs the natural choice for rapid iteration during active development.

## spm

SPM has a slow dev loop. Every change requires rebuilding the `.spm` archive (`spm build`), uploading it to the SPM repository server, updating the `SPM-METADATA` index, and reinstalling on the target master (`spm install`). There is no watch mode or hot-reload. For local testing, developers typically bypass SPM entirely and copy files directly into `extmods/` or `file_roots/`, which means SPM is not actually being tested in the development path.

## salt-bundle

salt-bundle sits between gitfs and SPM. For local formula development, salt-bundle supports a `path`-type repository that symlinks a local directory directly into the vendor directory (`symlink_path_package_to_vendor`), so changes to the source formula are reflected immediately without rebuilding or uploading. For shared or published formulas, the loop involves incrementing the formula version, running `salt-bundle formula pack` to build the `.tgz`, publishing via `salt-bundle repo release`, and then running `salt-bundle project update` in the consumer project. This is more involved than gitfs but provides the same reproducibility guarantees in the development environment as in production.
