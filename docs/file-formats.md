# File Formats Reference

Salt Bundle uses YAML for package metadata, dependency manifests, repository
indexes, and lock files.

| File            | Location                  | Purpose                               |
|-----------------|---------------------------|---------------------------------------|
| `FORMULA`       | Formula package root      | Metadata for a Salt formula           |
| `EXTENSION`     | Extension package root    | Metadata for Salt extension (saltext) |
| `FORMULAIGNORE` | Next to FORMULA/EXTENSION | Exclude files from packaging          |
| `Saltfile`      | Project root              | Declared project dependencies         |
| `Saltfile.lock` | Project root              | Resolved, reproducible dependencies   |
| `index.yaml`    | Repository root           | Available package versions            |

---

## FORMULA

Package metadata for Salt formulas. Contains `.sls` files with optional Salt
module directories (`_modules/`, `_states/`, etc.).

```yaml
# ── Required ─────────────────────────────────────────────

name: string                    # Package name (lowercase, [a-z0-9_-])
version: string                 # Semantic version (MAJOR.MINOR.PATCH[-pre][+build])

# ── Optional: description ────────────────────────────────

description: string | null      # Full description
summary: string | null          # One-line summary

# ── Optional: Salt compatibility ─────────────────────────

minimum_version: string | null  # Min Salt version ("3006")
maximum_version: string | null  # Max Salt version ("3009")

# ── Optional: target OS ──────────────────────────────────

os: string | null               # Target OS ("Ubuntu", "CentOS")
os_family: string | null        # OS family ("Debian", "RedHat")

# ── Optional: packaging ─────────────────────────────────

top_level_dir: string | null    # Relative path to state files subdirectory
                                # Use when formula content is not in the package root
                                # Must be relative, no ".." components
                                # "." and empty are treated as omitted

# ── Optional: dependencies ───────────────────────────────

dependencies:                   # List of formula dependencies
  - name: string                #   Package name (required)
    version: string | null      #   Semver constraint ("^1.0.0", "~2.3", ">=1.0,<2.0")
    url: string | null          #   Repository URL override

  - string                      # Short form: package name only (resolves to latest)

# ── Optional: people ─────────────────────────────────────

maintainers:                    # Current maintainers
  - name: string                #   Name (required)
    email: string | null        #   Email
    github: string | null       #   GitHub username

authors:                        # Original authors (same structure as maintainers)
  - name: string
    email: string | null
    github: string | null

# ── Optional: metadata ───────────────────────────────────

keywords:                       # Tags for search/categorization
  - string

license: string | null          # License identifier ("Apache-2.0", "MIT")
website: string | null          # Project website URL
source: string | null           # Source repository URL
issues: string | null           # Issue tracker URL
filtered_args:                  # Arguments to filter during processing
  - string
```

### Formula directory layout

```text
nginx/
├── FORMULA
├── FORMULAIGNORE
├── init.sls
├── defaults.sls
├── nginx/
│   └── nginx.conf.jinja
├── _modules/
│   └── nginx_status.py
├── _states/
│   └── nginx_site.py
└── _grains/
    └── nginx_info.py
```

### Formula with top_level_dir

```text
my-formula/
├── FORMULA              ← top_level_dir: formula
├── FORMULAIGNORE
├── README.md
├── ci/
└── formula/             ← state files here
    ├── init.sls
    └── _modules/
        └── mymod.py
```

### Example FORMULA

```yaml
name: nginx
version: 2.1.0
description: Nginx web server with SSL and reverse proxy support

minimum_version: "3006"
maximum_version: "3009"

maintainers:
  - name: DevOps Team
    email: devops@example.com

keywords:
  - webserver
  - reverse-proxy

dependencies:
  - name: common
    version: "^1.0.0"
  - name: firewall
    version: "~2.3.0"

source: https://github.com/example/salt-nginx
license: Apache-2.0
```

---

## EXTENSION

Package metadata for Salt extensions (saltext packages). Uses the standard
SaltStack extension layout under `src/saltext/<name>/`.

```yaml
# ── Required ─────────────────────────────────────────────

name: string                    # Extension name ("saltext-monitoring")
version: string                 # Semantic version

# ── Optional: description ────────────────────────────────

description: string | null      # Full description
summary: string | null          # One-line summary

# ── Optional: Salt compatibility ─────────────────────────

minimum_version: string | null  # Min Salt version
maximum_version: string | null  # Max Salt version

# ── Optional: Python dependencies ────────────────────────

python_requires:                # Python packages needed at runtime
  - name: string                #   PyPI package name (required)
    version: string | null      #   Version constraint (">=5.9.0")

# ── Optional: Salt dependencies ──────────────────────────

dependencies:                   # Salt formula/extension dependencies
  - name: string                #   Package name (required)
    version: string | null      #   Semver constraint
    url: string | null          #   Repository URL override

  - string                      # Short form: package name only

# ── Optional: conflicts ──────────────────────────────────

conflicts:                      # Packages that cannot coexist
  - name: string                #   Conflicting package name (required)
    reason: string | null       #   Why it conflicts

# ── Optional: people ─────────────────────────────────────

maintainers:                    # Current maintainers
  - name: string                #   Name (required)
    email: string | null        #   Email
    github: string | null       #   GitHub username

authors:                        # Original authors (same structure)
  - name: string
    email: string | null
    github: string | null

# ── Optional: metadata ───────────────────────────────────

license: string | null          # License identifier
website: string | null          # Project website URL
source: string | null           # Source repository URL
issues: string | null           # Issue tracker URL
```

### Extension directory layout

```text
saltext-monitoring/
├── EXTENSION
├── FORMULAIGNORE
└── src/
    └── saltext/
        └── monitoring/          ← auto-detected by name
            ├── __init__.py
            ├── modules/         ← execution modules
            │   └── monitoring.py
            ├── states/          ← state modules
            │   └── monitoring.py
            └── utils/           ← utility modules
                └── helpers.py
```

### Example EXTENSION

```yaml
name: saltext-monitoring
version: 1.0.0
description: Salt extension for host monitoring and health checks

minimum_version: "3006"
maximum_version: "3009"

python_requires:
  - name: psutil
    version: ">=5.9.0"

conflicts:
  - name: saltext-metrics
    reason: Both provide monitoring.* execution module namespace

maintainers:
  - name: SRE Team
    email: sre@example.com

source: https://github.com/example/saltext-monitoring
license: Apache-2.0
dependencies: []
```

---

## FORMULA vs EXTENSION

| Feature            | FORMULA                       | EXTENSION                                      |
|--------------------|-------------------------------|------------------------------------------------|
| Marker file        | `FORMULA`                     | `EXTENSION`                                    |
| State files        | Root or `top_level_dir/`      | `src/saltext/<name>/`                          |
| Module dirs        | `_modules/`, `_states/`, etc. | `src/saltext/<name>/modules/`, `states/`, etc. |
| `top_level_dir`    | Supported                     | Not applicable                                 |
| `os` / `os_family` | Supported                     | Not applicable                                 |
| `keywords`         | Supported                     | Not applicable                                 |
| `python_requires`  | Not applicable                | Supported                                      |
| `conflicts`        | Not applicable                | Supported                                      |

---

## FORMULAIGNORE

Exclude files from packaging. Syntax identical to `.gitignore`.
Placed next to `FORMULA` or `EXTENSION`.

Built-in exclusions (always applied):

```
.git/**
__pycache__/**
*.pyc
*.pyo
tests/**
.pytest_cache/**
*.egg-info/**
```

Example `FORMULAIGNORE`:

```gitignore
# CI/CD
.github
.gitlab-ci.yml

# IDE
.idea
.vscode

# Development
.venv
.env
*.log

# Sensitive files
*.key
*.pem
secrets/
```

When `top_level_dir` is set in `FORMULA`, patterns in `FORMULAIGNORE` are matched
relative to the `top_level_dir` path, not the repository root.

---

## Saltfile

Project dependencies declared in the project root.

```yaml
vendor_dir: string              # Where to install packages (default: "vendor")

dependencies:                   # List of required packages
  - name: string                #   Package name (required)
    version: string | null      #   Semver constraint
    source: string | null       #   Repository URL with index.yaml

runtime:                        # Optional runtime configuration
  top_bundle_file: string       #   Path to activation rules (default: "salt/top_bundle.sls")
  cache_dir: string             #   Runtime cache directory (default: ".salt-bundle/runtime")
  max_workers: integer          #   Parallel execution workers (default: 4, min: 1)
  require_bundle_top: boolean   #   Fail if top_bundle.sls missing (default: false)
```

### Example Saltfile

```yaml
vendor_dir: vendor

dependencies:
  - name: nginx
    version: "^2.1.0"
    source: https://packages.example.com/salt
  - name: mysql
    version: "~5.7.0"

runtime:
  top_bundle_file: salt/top_bundle.sls
  max_workers: 8
```

---

## Saltfile.lock

Resolved dependencies with pinned versions. Generated by `salt-bundle project update`.

```yaml
dependencies:
  nginx:
    version: 2.1.0
    repository: https://packages.example.com/salt
    url: nginx/nginx-2.1.0.tgz
    digest: sha256:abc123...
    type: formula
    dependencies:
      common: "1.5.2"
```

---

## index.yaml

Repository package index. Generated by `salt-bundle repo index DIRECTORY`.

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
