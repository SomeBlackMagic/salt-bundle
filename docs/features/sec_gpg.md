# GPG Signature

## gitfs

gitfs does not support GPG verification of git content at the Salt layer. Git itself supports signed commits and signed tags (`git tag -s`), and a repository server can enforce that only signed commits are accepted, but Salt's gitfs backend does not check GPG signatures before serving files. There is no configuration option in gitfs to require or validate tag/commit signatures. Operators who need GPG verification must implement it outside of Salt (e.g., in a CI pipeline that validates before pushing to the remote).

## spm

spm does not support GPG signing or verification of `.spm` packages or the `SPM-METADATA` index. The spm toolchain was designed without a cryptographic signing layer. There are no `spm` subcommands for signing packages, and no verification step during `spm install`. This is a known gap in the spm security model.

## salt-bundle

salt-bundle does not currently implement GPG signing or verification. The `IndexEntry` model in `dependencies/index_models.py` has a SHA256 digest but no GPG signature field, and `index.yaml` version `v1` has no signature block. Integrity comes from content addressing: the digest in the index and lock file ensures the downloaded archive matches what was indexed, but does not attest authorship. The current trust anchor is the repository transport (normally HTTPS) plus SHA256 verification.
