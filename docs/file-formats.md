# File formats

Salt Bundle uses YAML for package metadata, dependency manifests, repository
indexes, and lock files.

| File | Location | Purpose |
|---|---|---|
| `FORMULA` | Formula package root | Metadata for a Salt formula. |
| `EXTENSION` | Extension package root | Metadata for pure Python Salt modules. |
| `Saltfile` | Project root | Declared project dependencies. |
| `Saltfile.lock` | Project root | Resolved, reproducible dependencies. |
| `index.yaml` | Repository root | Available package versions. |

## FORMULA

FORMULA packages contain one or more `.sls` files, with optional Salt module
directories such as `_modules/` and `_states/`.

```yaml
name: nginx
version: 2.1.0
description: Install and configure Nginx
minimum_version: "3006"
dependencies:
  - name: common
    version: "^1.0.0"
    url: https://packages.example.test/salt
```

`name` must match `^[a-z0-9_-]+$`; `version` must be a semantic version.
`top_level_dir`, if specified, must be a relative path inside the package.

## EXTENSION

EXTENSION packages contain at least one supported Salt module directory and do
not require `.sls` files.

```yaml
name: example-extension
version: 1.0.0
description: Custom Salt execution modules
python_requires:
  - name: requests
    version: ">=2.28.0"
dependencies:
  - name: shared-extension
    version: "^1.0.0"
conflicts:
  - name: legacy-extension
    reason: Provides the same execution module
```

An extension may depend only on extensions. `python_requires` and `conflicts`
are metadata; they are not installed or resolved automatically.

## Saltfile

```yaml
vendor_dir: vendor
dependencies:
  - name: nginx
    version: "^2.1.0"
    source: https://packages.example.test/salt
```

`dependencies` is always a list. `source` must identify a repository with an
`index.yaml`; it is not a direct archive or Git repository URL.

## Saltfile.lock

```yaml
dependencies:
  nginx:
    version: 2.1.0
    repository: https://packages.example.test/salt
    url: nginx/nginx-2.1.0.tgz
    digest: sha256:abc123...
    type: formula
```

## index.yaml

```yaml
apiVersion: v1
generated: 2026-01-01T00:00:00
packages:
  nginx:
    - version: 2.1.0
      url: nginx/nginx-2.1.0.tgz
      digest: sha256:abc123...
      type: formula
      dependencies:
        - name: common
          version: "^1.0.0"
```

Generate an index with `salt-bundle repo index DIRECTORY`.
