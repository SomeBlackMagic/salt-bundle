# Storage History

## gitfs

gitfs retains the full Git history of every configured remote. The on-disk cache is a bare Git repository (`git clone --mirror`), so all commits, branches, tags, and the full reflog are present locally. Salt can serve any branch or tag as a separate environment simultaneously — switching an environment to a different tag requires no re-download, only a ref checkout. This full history is both an advantage (rollback is a ref change) and a cost: the cache size grows with the repository history and cannot easily be pruned without re-cloning.

## spm

spm keeps no history whatsoever. Installing a new version of a package overwrites the previous installation in `extmods/` with no backup or record of what was there before. There is no rollback mechanism built into spm. The only history available is what the underlying package repository exposes (a list of available versions in `SPM-METADATA`), but once a version is installed and a newer one replaces it, the previous state is gone from the filesystem.

## salt-bundle

salt-bundle does not maintain a history of installed vendor/ states. Each `salt-bundle install` call clears the existing subdirectory for a package (`shutil.rmtree(target_dir)` in `vendor.py:install_package_to_vendor`) before extracting the new version. However, the lock file (`.salt-dependencies.lock`) acts as an immutable record of the exact version, repository, URL, and SHA256 digest that was last installed for each dependency. This allows reconstruction of any prior state by re-running `install` with a committed lock file, but the `vendor/` tree itself contains only the currently installed snapshot.
