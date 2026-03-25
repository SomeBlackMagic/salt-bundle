# GPG Signature

## gitfs

gitfs does not support GPG verification of git content at the Salt layer. Git itself supports signed commits and signed tags (`git tag -s`), and a repository server can enforce that only signed commits are accepted, but Salt's gitfs backend does not check GPG signatures before serving files. There is no configuration option in gitfs to require or validate tag/commit signatures. Operators who need GPG verification must implement it outside of Salt (e.g., in a CI pipeline that validates before pushing to the remote).

## spm

spm does not support GPG signing or verification of `.spm` packages or the `SPM-METADATA` index. The spm toolchain was designed without a cryptographic signing layer. There are no `spm` subcommands for signing packages, and no verification step during `spm install`. This is a known gap in the spm security model.

## salt-bundle

salt-bundle does not currently implement GPG signing or verification. The `IndexEntry` model in `models/index_models.py` contains a `digest` field for SHA256 content verification but no field for a GPG signature. The `index.yaml` repository index format (schema version `v1`) has no signature block. Integrity is provided exclusively through SHA256 content addressing: the digest recorded in the index and lock file ensures that the downloaded archive byte-for-byte matches what was indexed, but does not provide authorship attestation. GPG support (signing of the `index.yaml` by the repository publisher and verification during `fetch_index()` / `download_package()`) is listed as a future enhancement. Until implemented, the trust anchor is the HTTPS channel to the repository server combined with SHA256 digest verification.
