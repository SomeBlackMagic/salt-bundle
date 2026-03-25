# Onboarding

## gitfs

Getting started with gitfs requires no additional tooling beyond a running Salt master. The operator adds a `gitfs_remotes` entry to `master` config, pointing to a Git repository URL, and restarts the master. Salt immediately begins serving states from the remote branch. The barrier to entry is very low for anyone already familiar with Git — there is no packaging step, no CLI to install, and no separate artifact to build. The main prerequisite is that the Salt master can reach the Git remote over the network.

## spm

SPM has a higher onboarding cost. The formula author must create a `FORMULA` metadata file, run `spm build` to produce a `.spm` archive, host it in an SPM repository (an HTTP server with an `SPM-METADATA` index file), configure `spm_repos_config` on the master, and then install with `spm install`. There is no interactive scaffolding for new formulas, and the tooling is not well documented, making the initial setup non-obvious. Consuming a formula requires understanding both the repository format and the SPM database on the master filesystem.

## salt-bundle

salt-bundle requires initial familiarity with two separate concepts: the project manifest (`.salt-dependencies.yaml`) and the formula manifest (`.saltbundle.yaml`). The CLI provides guided scaffolding: `salt-bundle project init` walks the user through project name and version interactively, and `salt-bundle formula init` does the same for a formula. After init, the workflow is: add a repository with `salt-bundle repo add`, declare dependencies in `.salt-dependencies.yaml`, run `salt-bundle project update` to resolve and vendor. The additional concepts (lock file, vendor dir, loader plugin) add onboarding friction compared to gitfs, but less than SPM because every step is driven by a single CLI with inline help.
