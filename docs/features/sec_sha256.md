# SHA256 Verification

## gitfs

gitfs performs no SHA256 verification of formula content. Git's own object integrity uses SHA1 hashes for pack objects, but gitfs does not expose or validate these at the formula level. There is no mechanism to declare an expected hash for a specific formula version and verify it before serving files to minions. An attacker with write access to the git remote or the local gitfs cache can alter formula content without detection.

## spm

spm does not implement SHA256 verification for package downloads or installed files. The `.spm` package format and `SPM-METADATA` index contain no cryptographic digest fields. There is no checksum validation between the downloaded archive and what is installed into `extmods/`. The absence of integrity verification is a documented limitation of the spm toolchain.

## salt-bundle

salt-bundle enforces SHA256 verification at multiple points in the supply chain. When `generate_index()` in `repository.py` builds a repository index, it computes a SHA256 digest for every `.tgz` archive using `calculate_sha256()` from `utils/hashing.py` and stores it in `index.yaml` in the format `sha256:<hex>`. The `IndexEntry` model (`models/index_models.py`) declares `digest` as a required field. When `download_package()` downloads an archive, it verifies the digest against the expected value from the index using `verify_digest()` before returning the path; if verification fails, the corrupted cache file is deleted and a `ValueError` is raised. The lock file (`models/lock_models.py`) also records the digest for each locked dependency so that reinstallation from the lock file can reuse cached archives only after passing the same digest check. The only exception is `type: path` repositories (local development), where the digest field is set to the literal string `"path"` and no checksum is computed.
