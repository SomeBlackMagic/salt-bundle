# Runtime access

## gitfs

gitfs provides full runtime access to formula files. The Salt master continuously polls configured Git remotes (controlled by `gitfs_update_interval`) and updates the local gitfs cache without restarting. Changes pushed to a tracked branch or tag become available to minions on the next update cycle. This means a state file can be edited in the repository and applied to minions within minutes, with no deployment step. This live coupling is the defining characteristic of gitfs — it is designed for runtime access and continuous delivery of configuration.

## spm

spm has no runtime access to package sources. Packages are installed from `.spm` archives at a specific point in time, and the installed files are static on disk. Updating a formula requires explicitly running `spm install` again with a new version of the package. There is no mechanism for the master to automatically detect or pull updates from an spm repository. Once installed, the files are decoupled from their origin.

## salt-bundle

salt-bundle has no runtime access to remote repositories. Packages are resolved, downloaded, and unpacked into `vendor/` during `salt-bundle install` or `salt-bundle update`. The resulting `vendor/` directory is a static snapshot; neither the Salt master nor the minion communicates with any repository server at runtime. The `bundlefs` fileserver backend and the `ext/loader.py` hooks read only from the local filesystem. This is by design — salt-bundle treats the vendored state as an immutable artifact, which eliminates runtime network dependencies and ensures deterministic execution across all minions.
