# Learning curve

## gitfs

gitfs has a low learning curve for anyone with basic Git and Salt knowledge. The entire configuration is a handful of keys in `master` config (`gitfs_remotes`, `gitfs_provider`, `gitfs_base`, optionally `gitfs_saltenv_whitelist`). No new tooling needs to be learned. The concepts — remote URL, branch, environment mapping — are already familiar to Git users. The main subtleties are understanding gitfs cache behavior and Salt environment-to-branch mapping, which can be read in the Salt documentation.

## spm

SPM has a high learning curve. The operator must learn the `FORMULA` file schema, the SPM build and repository layout, the `spm_repos_config` syntax on the master, and the SPM CLI commands. The documentation is sparse and the tooling is not widely used in the community, so there are few practical examples. The SPM database format is not user-friendly, and the relationship between SPM-installed files and Salt's loader is implicit and poorly documented.

## salt-bundle

salt-bundle has a medium learning curve. The core concepts borrow from familiar package managers (npm, pip, Cargo): a project manifest with version constraints, a lock file with pinned versions, a vendor directory, and a CLI for resolving and installing. Developers familiar with any modern package manager will find the model intuitive. The additional Salt-specific concepts — the loader plugin registration via entry points, the `bundlefs` fileserver backend, the `ext_pillar` hook — require understanding how Salt's internal extension loading works. The CLI provides inline help for every command, and the config files (`.salt-dependencies.yaml`, `.saltbundle.yaml`) are plain YAML validated by Pydantic models with descriptive error messages.
