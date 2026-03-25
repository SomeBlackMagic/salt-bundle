<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://cdn.jsdelivr.net/gh/SomeBlackMagic/salt-bundle@master/docs/logo.png" width="350" alt="Salt Bandle Logo">
  <img src="https://cdn.jsdelivr.net/gh/SomeBlackMagic/salt-bundle@master/docs/logo.png" width="350" alt="Salt Bandle Logo">
</picture>

![PyPI - Version](https://img.shields.io/pypi/v/salt-bundle)

Salt Bundle is a package manager for Salt formulas, similar to pip, npm, or Helm. It allows you to version, publish, and install Salt formulas with dependency management and reproducible builds.

## Quick Links

### For Formula Publishers
- [Publishing Guide](publishing-guide.md) - How to create and publish formulas
- [Formula Configuration](formula-configuration.md) - `.saltbundle.yaml` format for formulas
- [Repository Setup](repository-setup.md) - Setting up your own repository

### For Formula Consumers
- [Installation Guide](installation-guide.md) - Installing and using formulas
- [Project Configuration](project-configuration.md) - `.saltbundle.yaml` format for projects
- [Version Constraints](version-constraints.md) - Semantic versioning and dependency resolution

### Reference
- [CLI Reference](cli-reference.md) - Complete command-line interface documentation
- [File Formats](file-formats.md) - All configuration file formats
- [CI/CD Integration](cicd-integration.md) - GitHub Actions and GitLab CI examples

## Overview

### What is Salt Bundle?

Salt Bundle provides:

1. **Version Management** - Use semantic versioning for Salt formulas
2. **Dependency Resolution** - Declare and automatically resolve formula dependencies
3. **Package Distribution** - Publish formulas to HTTP or local repositories
4. **Reproducible Builds** - Lock files ensure consistent deployments
5. **Automatic Integration** - Salt loader plugin auto-discovers formulas (no config changes needed)
6. **Manual Integration** - Also works with existing Salt setups via `file_roots`

### Key Concepts

- **Formula** - A Salt state directory with `.sls` files and metadata
- **Package** - A versioned `.tgz` archive of a formula
- **Repository** - HTTP/file location containing packages and an index
- **Project** - Your infrastructure code that depends on formulas
- **Vendor Directory** - Local folder where dependencies are installed
- **Salt Loader Plugin** - Automatic integration with Salt without config changes

## Quick Start

### Publishing a Formula

```bash
# Initialize formula metadata
cd my-formula
salt-bundle formula init

# Edit .saltbundle.yaml with your metadata

# Pack the formula
salt-bundle formula pack
# Creates: my-formula-1.0.0.tgz

# Generate repository index
mkdir -p /srv/salt-repo
cp my-formula-1.0.0.tgz /srv/salt-repo/
cd /srv/salt-repo
salt-bundle repo index
# Creates: index.yaml
```

### Using a Formula

```bash
# Initialize project
mkdir my-project
cd my-project
salt-bundle project init

# Add repository (global config)
salt-bundle repo add --name main --url https://example.com/salt-repo/

# Edit .salt-dependencies.yaml to add dependencies
# dependencies:
#   my-formula: "^1.0.0"

# Install dependencies
salt-bundle project install
# Installs to: vendor/my-formula/

# Use in Salt
salt-call --local \
  --file-root=/path/to/my-project/salt:/path/to/my-project/vendor \
  state.apply
```

## Installation

### From PyPI (when published)

```bash
pip install salt-bundle
```

### From Source

```bash
git clone https://github.com/SomeBlackMagic/salt-bundle.git
cd salt-bundle
pip install -e .
```

### Verify Installation

```bash
salt-bundle --help
```

## Basic Workflow

### For Publishers

1. Create a formula with Salt states
2. Add `.saltbundle.yaml` metadata
3. Pack into versioned archive
4. Publish to repository
5. Update repository index

See [Publishing Guide](publishing-guide.md) for details.

### For Consumers

1. Initialize project with `.saltbundle.yaml`
2. Add repositories
3. Declare dependencies with version constraints
4. Install dependencies (creates lock file)
5. Integrate with Salt via `file_roots`

See [Installation Guide](installation-guide.md) for details.

## Architecture

```
Publishers                     Repository                    Consumers
──────────                     ──────────                    ─────────

┌─────────────┐               ┌─────────────┐              ┌─────────────┐
│   Formula   │               │  index.yaml │              │  .saltbundle│
│  Directory  │──pack─────▶   │             │              │    .yaml    │
│             │               │  formula-   │              │             │
│ - init.sls  │               │   1.0.0.tgz │◀────fetch────│ dependencies│
│ - .saltbundle               │             │              │             │
│   .yaml     │               │  formula-   │              └─────────────┘
└─────────────┘               │   1.0.1.tgz │                     │
                              └─────────────┘                  install
                                                                  │
                                                                  ▼
                                                           ┌─────────────┐
                                                           │   vendor/   │
                                                           │  formula/   │
                                                           │ - init.sls  │
                                                           └─────────────┘
```

## Features

### Semantic Versioning

- Full semver support: `1.2.3`, `1.2.3-beta.1`
- Version constraints: `^1.0.0`, `~1.2.3`, `>=1.0,<2.0`
- Automatic resolution to latest compatible version

### Dependency Management

- Declare dependencies in `.saltbundle.yaml`
- Automatic resolution across repositories
- Lock file for reproducible installations
- Repository-specific dependencies: `repo/package`

### Repository Management

- HTTP/HTTPS repositories
- Local file:// repositories
- Multiple repository support
- Package caching

### CI/CD Integration

- Automated release workflows
- GitHub Releases support
- GitHub Pages for index hosting
- GitLab CI compatible

## Configuration Files

### Formula: `.saltbundle.yaml`

```yaml
name: my-formula
version: 1.0.0
description: My Salt formula

maintainers:
  - name: Developer Name
    email: dev@example.com

salt:
  min_version: "3006"
  max_version: "3009"

dependencies:
  - name: common
    version: "^1.0"
```

### Project: `.saltbundle.yaml`

```yaml
project: my-infrastructure
version: 0.1.0
vendor_dir: vendor

repositories:
  - name: main
    url: https://salt-formulas.example.com/

dependencies:
  nginx: "^2.0.0"
  mysql: "~5.7"
  main/redis: ">=6.0,<7.0"
```

### Lock File: `.salt-dependencies.lock`

```yaml
dependencies:
  nginx:
    version: 2.1.0
    repository: main
    url: https://salt-formulas.example.com/nginx-2.1.0.tgz
    digest: sha256:abc123...
```

## Common Use Cases

### Monorepo with Multiple Formulas

```bash
formulas/
  ├── nginx/
  │   ├── .saltbundle.yaml
  │   └── init.sls
  ├── mysql/
  │   ├── .saltbundle.yaml
  │   └── init.sls
  └── redis/
      ├── .saltbundle.yaml
      └── init.sls

# Release all formulas
cd formulas
salt-bundle repo release --formulas-dir . --provider local --pkg-storage-dir ../repo
```

### Single Formula Repository

```bash
# In formula repository
salt-bundle repo release --formulas-dir . --single --provider github

# With GitHub:
export GITHUB_TOKEN=ghp_xxx
export GITHUB_REPOSITORY=owner/repo
salt-bundle repo release --formulas-dir . --single --provider github
```

### Private Repository

```bash
# Add private repository
salt-bundle repo add --name private --url https://private.example.com/repo/

# Use in project
dependencies:
  private/internal-formula: "^1.0.0"
```

## Integration with Salt

### Option 1: Automatic Salt Loader Plugin (Recommended)

After `pip install salt-bundle`, Salt automatically discovers formulas in your project's `vendor/` directory.

**No configuration changes needed!**

```bash
# Install salt-bundle
pip install salt-bundle

# Navigate to project with .saltbundle.yaml
cd my-project

# Run Salt commands - formulas auto-discovered from vendor/
salt-call state.apply nginx
salt-ssh '*' state.apply mysql

# Verify loader is working
salt-call pillar.get saltbundle
```

**How it works:**
1. Salt automatically loads the plugin via entry points
2. Plugin searches for `.saltbundle.yaml` in current directory
3. Reads `vendor_dir` from config
4. Automatically adds formulas to `file_roots`

See [examples/project/README.md](../examples/project/README.md) for detailed examples.

### Option 2: Wrapper Script

```bash
#!/usr/bin/env bash
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENDOR_DIR="${PROJECT_ROOT}/vendor"
SALT_DIR="${PROJECT_ROOT}/salt"

salt-call --local \
  --file-root="${SALT_DIR}:${VENDOR_DIR}" \
  "$@"
```

### Option 3: Salt Master Config

```yaml
# /etc/salt/master
file_roots:
  base:
    - /srv/salt
    - /srv/my-project/vendor
```

### Option 4: Salt Minion Config

```yaml
# /etc/salt/minion
file_roots:
  base:
    - /srv/salt
    - /srv/my-project/vendor
```

## Support and Contributing

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/SomeBlackMagic/salt-bundle/issues)
- **Documentation**: This documentation is in the `docs/` directory
- **Contributing**: Pull requests welcome!

## License

Apache License 2.0

## Next Steps

- **Publishers**: Read the [Publishing Guide](publishing-guide.md)
- **Consumers**: Read the [Installation Guide](installation-guide.md)
- **CI/CD**: Check [CI/CD Integration](cicd-integration.md)
- **Reference**: See [CLI Reference](cli-reference.md)

## TODO

### Dependency Resolution

- [ ] **Conflict resolution** — when two packages require incompatible versions of the same dependency, resolution silently picks the first-resolved version (`if pkg_name in resolved_packages: continue` in `cli/project/update.py`). A proper conflict detection and error reporting mechanism is needed.
- [ ] **Version compatibility check** — `# TODO: Check version compatibility` comment exists in `cli/project/update.py`; Salt `min_version` / `max_version` fields in formula metadata are parsed but never enforced at install time.
- [ ] **Dependency graph output** — no command to visualize or inspect the resolved dependency graph; useful for debugging complex dependency trees.

### Pillar Support

- [ ] **Auto-discovery of pillar data** — the `ext_pillar` plugin currently returns only project metadata (`project_dir`, `vendor_dir`, `formulas`, `formula_paths`). Pillar data files (`pillar/*.sls`) from individual formulas are not automatically merged into the pillar namespace.

### Platform Integration

- [ ] **GitLab full support** — the `GitLabReleaseProvider` is partially implemented; package release to GitLab Package Registry and index publishing to GitLab Pages need to be completed and tested.
- [ ] **salt-ssh stability** — the loader plugin is bypassed by salt-ssh's thin-client bundling path. A workaround exists (duplicated entry-point registrations with a `# TODO black magic` comment), but a proper solution is needed.

### Security

- [ ] **GPG signature verification** — packages are currently verified only by SHA256 digest. GPG signing of packages and signature verification on install would improve supply chain security.

### UX / DX

- [ ] **Dry-run for `project update`** — show what would change without modifying the lock file or vendor directory (mentioned in version-constraints.md as a planned feature).
- [ ] **`--timeout` flag** — mentioned in cicd-integration.md but not implemented in CLI code.
- [ ] **`formula sync` improvements** — `formula sync` copies modules to the Salt cache for use without the loader plugin; integration with salt-ssh thin client needs hardening.
