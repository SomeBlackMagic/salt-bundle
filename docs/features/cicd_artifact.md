# Artifact

## gitfs

gitfs produces no build artifact. The deliverable is a Git commit — a reference to a tree object in a remote repository. There is no file to archive, sign, version-pin, cache in a registry, or attach to a CI pipeline run. The consequence is that there is no immutable record of what was deployed: a branch pointer can be moved, history can be rewritten, and the same branch name can serve different content at different times.

## spm

The artifact produced by spm is a `.spm` file — a gzip-compressed tar archive named `{formula}-{version}-{release}.{arch}.spm`. The archive contains the formula files plus a `FORMULA` metadata file. The `.spm` format is specific to Salt Stack and is consumed by the `spm install` command on a master or minion. There is no integrity digest stored alongside the artifact in a standard index, and there is no tooling in spm itself for publishing `.spm` files to an HTTP repository or attaching them to a version control release event.

## salt-bundle

The artifact is a `.tgz` file named `{name}-{version}.tgz` (e.g., `apache-1.2.0.tgz`), produced by `pack_formula()` using Python's `tarfile` module in `w:gz` mode. Every artifact is registered in `index.yaml` with a `digest` field in the format `sha256:<hex>`, calculated by `calculate_sha256()` in `utils/hashing.py` using 8192-byte chunked reads. The `IndexEntry` model (in `models/index_models.py`) stores the version, download URL, digest, creation timestamp, keywords, maintainers, and dependency list. This makes each artifact independently verifiable: `verify_digest()` re-hashes the downloaded file and compares it against the stored digest before installation.
