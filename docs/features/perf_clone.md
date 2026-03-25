# Clone overhead

## gitfs

Clone overhead is high and proportional to repository history depth. When gitfs encounters a new remote for the first time, it executes `git clone` into the local gitfs cache directory (typically `/var/cache/salt/master/gitfs/`). For repositories with long history or large binary files, this initial clone can take tens of seconds to several minutes and consume significant disk space. With multiple formulas stored in separate repositories (the recommended gitfs topology), each repository is cloned independently, multiplying the overhead. The clone is a one-time cost per remote, but on a fresh Salt master or after cache invalidation, it becomes a blocking operation before any states can be served.

## spm

spm has no clone step and therefore no clone overhead. Packages are downloaded as individual `.spm` archives from an HTTP endpoint. There is no Git history to fetch, no object database to build, and no local clone to maintain. The download cost is proportional only to the size of the specific package being installed.

## salt-bundle

salt-bundle has no clone step and no clone overhead. Packages are downloaded as `.tgz` archives from an HTTP URL or GitHub release asset. The download is a single HTTP GET per package; there is no Git protocol involved. The `repository.download_package()` function fetches only the specific archive for the locked version, not the entire repository history. For local `path`-type repositories (used in development), no download occurs at all — the vendor entry is a symlink to the local formula directory created by `symlink_path_package_to_vendor()`.
