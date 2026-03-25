# Core Model

## gitfs

gitfs is a **fileserver backend** for Salt master. It does not manage packages or versions of Salt formulas — instead, it mounts one or more Git repositories directly as a virtual filesystem from which Salt serves `.sls` files, templates, and static files to minions. The Salt master clones each configured repository into its local gitfs cache (typically under `/var/cache/salt/master/gitfs/`) and serves files from there on every request. gitfs has no concept of packaging, metadata files, or dependency declarations: a repository is simply a tree of files. The model requires a live Salt master to serve content; the master itself acts as the only control point for what formulas are available to minions.

## spm

spm (Salt Package Manager) is a **package manager** built into Salt that installs pre-built formula packages onto the Salt master or minion. A package is a `.spm` archive containing Salt states, modules, and a `FORMULA` metadata file. spm installs packages into a fixed path (e.g., `/srv/spm/salt/`) and updates `file_roots` so that Salt can find the installed states. The model is similar to a traditional OS package manager (yum/apt), with a repository index called `SPM-METADATA` listing available packages. There is no local project file that tracks what is installed; state is tracked by the presence of installed files on disk.

## salt-bundle

salt-bundle is a **package manager with a dependency resolution system**, implemented as a standalone Python CLI tool (`salt-bundle`). The model is project-centric: a project directory contains a manifest file `.salt-dependencies.yaml` (a `ProjectConfig` Pydantic model) that declares dependencies and repositories. Resolved dependencies are downloaded as `.tgz` archives, verified by SHA256 digest, and unpacked into a local `vendor/` directory. The tool is fully decoupled from the Salt master: it runs locally (or in CI) and produces a vendor tree that Salt then consumes through a loader plugin. Package metadata is defined in `.saltbundle.yaml` files using a `PackageMeta` Pydantic model with strict semver versioning.
