# SHA256 Verification

## gitfs

gitfs performs no SHA256 verification of formula content. Git's own object integrity uses SHA1 hashes for pack objects, but gitfs does not expose or validate these at the formula level. There is no mechanism to declare an expected hash for a specific formula version and verify it before serving files to minions. An attacker with write access to the git remote or the local gitfs cache can alter formula content without detection.

## spm

spm does not implement SHA256 verification for package downloads or installed files. The `.spm` package format and `SPM-METADATA` index contain no cryptographic digest fields. There is no checksum validation between the downloaded archive and what is installed into `extmods/`. The absence of integrity verification is a documented limitation of the spm toolchain.

## salt-bundle

salt-bundle enforces SHA256 verification at multiple points in the supply chain. When `generate_index()` in `dependencies/index.py` builds a repository index, it computes a SHA256 digest for every archive and stores it in `index.yaml` as `sha256:<hex>`. The `IndexEntry` model in `dependencies/index_models.py` requires `digest`. When `download_package()` downloads an archive, it verifies the digest from the index before returning it; if verification fails, the corrupted cache file is deleted and an error is raised. `Saltfile.lock` records the same digest for each resolved dependency, so repeat installs can reuse cached archives only after the same check.
