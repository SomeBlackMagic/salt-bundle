# Supply Chain Control

## gitfs

gitfs provides no supply chain controls. There is no mechanism to restrict which git remotes may be configured, to verify the identity of a remote, or to audit the contents of what was fetched. SSH key authentication can restrict who can push to a remote, but this is enforced by the git hosting infrastructure, not by Salt or gitfs itself. Anyone who can modify the git remote (or perform a man-in-the-middle attack on an unprotected HTTP remote) can inject arbitrary Salt states and modules that will be served to all minions.

## spm

spm provides no supply chain controls. There is no concept of a trusted repository list, no verification that an installed package came from a specific source, and no audit trail linking an installed formula to a specific build pipeline. The `spm install` command accepts any `.spm` file from any source without verification.

## salt-bundle

salt-bundle implements supply chain control through several complementary mechanisms. The repository whitelist in `UserConfig` (`models/config_models.py`) exposes an `allowed_repos` field that can restrict which repository URLs are permitted at the user level. Every package installed from a remote repository must have its SHA256 digest match the value published in `index.yaml`, ensuring that the archive has not been tampered with between the repository server and the local cache. The lock file permanently records the full provenance chain for each dependency: package name, resolved version, repository name, download URL, and content digest. This lock file can be committed to version control and used as an auditable bill of materials. The `unpack_formula()` function in `package.py` also enforces a path-traversal safety check on every archive member before extraction, preventing archive-bomb or directory-escape attacks. GPG signing of repository indexes or packages is not yet implemented; SHA256 is the current root of trust.
