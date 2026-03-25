# Delivery Type

## gitfs

gitfs uses **runtime pull** delivery. The Salt master fetches files from the configured Git remote every time minions request them (or on a configurable polling interval). Files are never pre-packaged or pre-installed; they are resolved dynamically from the Git working tree at execution time. This means the formula content available to minions can change between two runs without any explicit deployment step — a new commit pushed to the tracked branch becomes available automatically on the next fetch cycle. The delivery is inherently tied to the runtime availability of the Git remote.

## spm

spm uses **install-time** delivery. A human operator (or a CI job) runs `spm install <package>` to explicitly download and unpack a `.spm` archive to the master's formula directory. After installation, the files are present on disk and served by Salt's standard fileserver without any further network access. The delivery step is separate from execution: once installed, formulas are available offline. However, the install operation itself is manual and stateless — spm does not record a dependency manifest or lock file, so there is no automated way to reproduce exactly the same set of installed packages on a new master.

## salt-bundle

salt-bundle uses **install-time (vendor)** delivery. The `salt-bundle project update` command resolves version constraints, downloads `.tgz` archives from configured HTTP or file repositories, verifies their SHA256 digest, and unpacks them into the project's `vendor/` directory. After this step, the vendor directory is a self-contained, offline-usable snapshot of all required formulas. Subsequent `salt-bundle project install` runs reproduce the identical set of packages by reading from the `.salt-dependencies.lock` file without re-running resolution. The vendor directory can be committed to version control or distributed as an artifact, making delivery fully reproducible and independent of runtime network access.
