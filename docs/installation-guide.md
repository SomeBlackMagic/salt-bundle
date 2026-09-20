# Installation guide

Salt Bundle installs FORMULA and EXTENSION packages declared by a project
`Saltfile`. A package source is always a repository directory containing an
`index.yaml` file.

## Create a project

```bash
mkdir my-infrastructure
cd my-infrastructure
salt-bundle project init
```

The command creates an empty manifest:

```yaml
vendor_dir: vendor
dependencies: []
```

A typical project layout is:

```text
my-infrastructure/
├── Saltfile
├── Saltfile.lock       # generated; commit it
├── salt/               # project states
├── pillar/             # project pillar data
└── vendor/             # generated packages
```

## Configure sources

You can give a dependency its own source, either an HTTP(S) repository or a
local directory. The URL/path identifies the directory that contains
`index.yaml`, not a package archive and not a Git repository.

```yaml
vendor_dir: vendor
dependencies:
  - name: nginx
    version: "^2.0.0"
    source: https://packages.example.test/salt

  - name: local-common
    source: file:///srv/salt-packages
```

For dependencies without `source`, add repositories to the global user
configuration:

```bash
salt-bundle repo add --name internal --url https://packages.example.test/salt
salt-bundle repo add --name local --url file:///srv/salt-packages
```

The configuration is stored in `~/.config/salt-bundle/config.yaml`:

```yaml
repositories:
  - name: internal
    url: https://packages.example.test/salt
```

## Resolve and install

After editing `Saltfile`, resolve the graph and install it:

```bash
salt-bundle project update
```

This selects compatible versions from every required `index.yaml`, writes
`Saltfile.lock`, downloads the archives, installs them into `vendor_dir`, and
asks Salt to sync extensions when `salt-call` is available.

For a reproducible install, use the existing lock file:

```bash
salt-bundle project install
# equivalent alias
salt-bundle project vendor
```

`Saltfile.lock` records the exact package version, repository URL, archive
path, SHA-256 digest, and package type. Do not edit it manually; commit it and
regenerate it with `project update` when changing dependencies.

## Dependency rules

- `dependencies` in `Saltfile` is a list of objects with `name`, optional
  `version`, and optional `source`.
- Constraints use semantic-version expressions such as `^2.0.0`, `~2.3.0`,
  or `>=1.0.0,<2.0.0`.
- Transitive dependencies come from the package metadata and are resolved the
  same way.
- A FORMULA may use FORMULA or EXTENSION dependencies. An EXTENSION may use
  only EXTENSION dependencies.

## Verify the installation

```bash
salt-bundle formula verify
find vendor -maxdepth 2 -name FORMULA -o -name EXTENSION
```

If a package cannot be resolved, first make sure its source ends at a
directory serving `index.yaml`, then check the package name and version range
against that index. A digest mismatch means the archive no longer matches the
published index; republish the archive and regenerate the repository index.

## Salt integration

The Salt loader integration discovers installed FORMULA and EXTENSION packages
from the configured vendor directory. Run states from the project directory so
the loader can find its `Saltfile`; `project update` and `project install` also
attempt `salt-call --local saltutil.sync_all` for extensions.

For manifest and index schemas, see [Project configuration](project-configuration.md)
and [File formats](file-formats.md). For repository publishing, see
[Repository setup](repository-setup.md).
