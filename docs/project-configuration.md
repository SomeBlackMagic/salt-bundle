# Saltfile

`Saltfile` is the dependency manifest for a Salt project. Place it in the
project root, next to `top.sls` or the project's primary Salt states.

```yaml
vendor_dir: vendor

dependencies:
  - name: nginx
    version: "^2.0.0"
    source: https://packages.example.test/salt

  - name: common
    version: ">=1.0.0"
```

`salt-bundle project update` resolves this manifest and writes `Saltfile.lock`.
`salt-bundle project install` installs exactly the versions in the lock file.

## Fields

### `vendor_dir`

Optional relative directory for installed packages. Its default is `vendor`.
Salt loader integration discovers FORMULA and EXTENSION packages from this
directory.

```yaml
vendor_dir: third_party/salt
```

### `dependencies`

An optional list of dependency objects. Each item has these fields:

| Field | Required | Meaning |
|---|---:|---|
| `name` | Yes | Package name from `index.yaml`. |
| `version` | No | SemVer constraint; omitted means the latest compatible version. |
| `source` | No | URL or local path of a repository containing `index.yaml`. |

`source` is a repository source, not a Git URL and not a direct package path.
For a local repository it may be a filesystem path or `file:///` URL.

```yaml
dependencies:
  - name: nginx
    version: "~2.3.0"
    source: file:///srv/salt-packages

  - name: common
```

When `source` is omitted, salt-bundle searches repositories registered in the
user configuration. Add one with:

```bash
salt-bundle repo add --name internal --url https://packages.example.test/salt
```

## Dependency rules

Package type is read from the repository index. A FORMULA can depend on a
FORMULA or EXTENSION. An EXTENSION can depend only on another EXTENSION;
resolution stops with an error if it selects a FORMULA.

Transitive dependencies use the `dependencies` field from package metadata.
An inline `url` on such a dependency selects the repository containing its
`index.yaml`; otherwise the source of the parent package is used.

## Saltfile.lock

`Saltfile.lock` is generated and should be committed to version control. It
records each resolved package's exact version, source repository, archive URL,
SHA-256 digest, and package type.

```yaml
dependencies:
  nginx:
    version: 2.3.1
    repository: https://packages.example.test/salt
    url: nginx/nginx-2.3.1.tgz
    digest: sha256:abc123...
    type: formula
```

Do not edit the lock file manually. Run `salt-bundle project update` after
changing Saltfile.

## Commands

```bash
# Create an empty Saltfile.
salt-bundle project init

# Resolve direct and transitive dependencies, then install them.
salt-bundle project update

# Reinstall exactly Saltfile.lock.
salt-bundle project install
```
