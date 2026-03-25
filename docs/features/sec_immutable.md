# Immutable Artifact

## gitfs

gitfs artifacts are mutable by design. A branch pointer can be moved forward or backward at any time on the remote, and after the next `fileserver.update` the Salt master will serve the updated content from the same environment name. Tags are more stable but can be force-pushed or deleted. There is no mechanism to declare that a particular artifact is frozen and must never change. This mutability is a fundamental property of the gitfs model: it enables live-update workflows but makes immutability impossible to guarantee.

## spm

spm artifacts are partially immutable. A `.spm` package file is a fixed archive once built, but the repository index (`SPM-METADATA`) can be updated to change which version is considered "latest", and there is no on-disk record binding a specific package name to a specific immutable digest. Reinstalling the same named version from a different build of the package will silently replace the previous installation. The lack of content-addressable caching means identity is based on version strings, not on content hashes.

## salt-bundle

salt-bundle artifacts are immutable by construction. Each `.tgz` package, once published to a repository and indexed, is identified by its SHA256 digest (`sha256:<hex>`) stored in `index.yaml`. The lock file (`.salt-dependencies.lock`) records this digest alongside the exact version, repository name, and download URL for every dependency. A given lock file entry therefore refers to a specific, content-addressed artifact that cannot be silently replaced: any change to the package content produces a different digest that will fail verification. The download cache itself is keyed by digest (`~/.cache/salt-bundle/packages/<sha256hex>.tgz`), making it impossible to store two different archives under the same cache entry. The only explicitly mutable case is `type: path` repositories (local development symlinks), which are exempted from digest verification and use the literal string `"path"` as the digest value.
