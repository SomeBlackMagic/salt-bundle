# Formula Publishing Guide

This guide explains how to create, package, and publish Salt formulas using Salt Bundle.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Creating a Formula](#creating-a-formula)
- [Formula Structure](#formula-structure)
- [Packaging](#packaging)
- [Publishing Methods](#publishing-methods)
- [Automated Publishing](#automated-publishing)
- [Best Practices](#best-practices)

## Prerequisites

- Salt Bundle installed: `pip install salt-bundle`
- A Salt formula (directory with `.sls` files)
- Access to a repository (local directory, HTTP server, or GitHub)

## Creating a Formula

### Step 1: Initialize Formula

```bash
cd my-formula
salt-bundle formula init
```

You'll be prompted for:
- **Formula name**: Package identifier (lowercase, alphanumeric, `-`, `_`)
- **Version**: Semantic version (e.g., `1.0.0`)
- **Description**: Optional description
- **Salt compatibility**: Min/max Salt versions

This creates `.saltbundle.yaml`:

```yaml
name: my-formula
version: 1.0.0
description: My awesome Salt formula
maintainers:
  - name: Your Name
    email: you@example.com
salt:
  min_version: "3006"
  max_version: "3009"
```

### Step 2: Add Formula Content

Your formula should have at least one `.sls` file:

```
my-formula/
├── .saltbundle.yaml
├── init.sls           # Required: main state file
├── install.sls        # Optional: additional states
├── config.sls
├── map.jinja          # Optional: configuration
├── defaults.yaml      # Optional: default values
├── files/            # Optional: static files
│   └── config.conf
├── templates/        # Optional: Jinja templates
│   └── app.conf.j2
└── _modules/         # Optional: custom modules
    └── mymodule.py
```

**Example `init.sls`:**

```yaml
{% from "my-formula/map.jinja" import config with context %}

my-formula-install:
  pkg.installed:
    - name: {{ config.package }}

my-formula-config:
  file.managed:
    - name: {{ config.config_file }}
    - source: salt://my-formula/templates/app.conf.j2
    - template: jinja
    - require:
      - pkg: my-formula-install

my-formula-service:
  service.running:
    - name: {{ config.service }}
    - enable: True
    - watch:
      - file: my-formula-config
```

### Step 3: Edit Metadata

Edit `.saltbundle.yaml` to add more details:

```yaml
name: my-formula
version: 1.0.0
description: Formula for managing MyApp service

maintainers:
  - name: Your Name
    email: you@example.com

keywords:
  - myapp
  - service
  - configuration

sources:
  - https://github.com/yourorg/my-formula

salt:
  min_version: "3006"
  max_version: "3009"

dependencies:
  - name: common
    version: "^1.0"
  - name: firewall
    version: "~2.3"
```

See [Formula Configuration](formula-configuration.md) for complete format.

## Formula Structure

### Required Files

- **`.saltbundle.yaml`**: Metadata (name, version, dependencies)
- **`init.sls`** or any `.sls`: At least one Salt state file

### Optional Components

- **States**: Additional `.sls` files
- **Pillar**: Data files for configuration
- **Jinja**: Templates and maps
- **Custom Modules**: `_modules/`, `_states/`, `_grains/`, etc.
- **Files**: Static files in `files/`
- **Documentation**: `README.md`, `CHANGELOG.md`

### Excluded Files

Salt Bundle automatically excludes:

- `.git/` - Git repository data
- `__pycache__/` - Python cache
- `*.pyc`, `*.pyo` - Compiled Python
- `.saltbundleignore` - Custom exclusions (like `.gitignore`)

**Example `.saltbundleignore`:**

```
tests/
*.log
temp/
.idea/
```

## Packaging

### Manual Packaging

```bash
cd my-formula
salt-bundle formula pack

# Output: my-formula-1.0.0.tgz
```

Specify output directory:

```bash
salt-bundle formula pack --output-dir /path/to/output
```

### Verify Package

Check package contents:

```bash
tar -tzf my-formula-1.0.0.tgz
```

### Version Update Workflow

```bash
# 1. Update version in .saltbundle.yaml
version: 1.0.1

# 2. Pack new version
salt-bundle formula pack

# Output: my-formula-1.0.1.tgz
```

## Publishing Methods

### Method 1: Local Repository

Best for: Private networks, testing, local development

```bash
# 1. Create repository directory
mkdir -p /srv/salt-repo

# 2. Copy package
cp my-formula-1.0.0.tgz /srv/salt-repo/

# 3. Generate index
cd /srv/salt-repo
salt-bundle repo index

# 4. Serve repository
# Option A: File system
salt-bundle repo add --name local --url file:///srv/salt-repo/

# Option B: HTTP server
cd /srv/salt-repo
python3 -m http.server 8080
# URL: http://localhost:8080/
```

See [Repository Setup](repository-setup.md) for details.

### Method 2: GitHub Releases

Best for: Open source, public formulas, CI/CD

```bash
# Setup
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
export GITHUB_REPOSITORY=yourorg/my-formula

# Release single formula
cd my-formula
salt-bundle repo release \
  --formulas-dir . \
  --single \
  --provider github

# Release multiple formulas
cd formulas/
salt-bundle repo release \
  --formulas-dir . \
  --provider github
```

**What happens:**
- Creates GitHub Release tagged `my-formula-1.0.0`
- Uploads `.tgz` as release asset
- Updates `index.yaml` in `gh-pages` branch

See [CI/CD Integration](cicd-integration.md#github-actions) for automation.

### Method 3: HTTP Repository

Best for: Production, CDN, enterprise

```bash
# 1. Pack formulas
salt-bundle formula pack

# 2. Upload to web server
scp my-formula-1.0.0.tgz user@server:/var/www/salt-repo/

# 3. Generate index on server
ssh user@server
cd /var/www/salt-repo
salt-bundle repo index --base-url https://salt-repo.example.com/

# Users add repository:
salt-bundle repo add --name prod --url https://salt-repo.example.com/
```

## Automated Publishing

### Release Command

The `salt-bundle repo release` command automates:

1. Discovery of formulas
2. Version checking (skip if already published)
3. Packaging
4. Upload to provider
5. Index update

#### Single Formula Release

```bash
cd my-formula
salt-bundle repo release \
  --formulas-dir . \
  --single \
  --provider local \
  --pkg-storage-dir /srv/salt-repo
```

#### Multiple Formulas Release

```bash
formulas/
  ├── nginx/
  ├── mysql/
  └── redis/

cd formulas
salt-bundle repo release \
  --formulas-dir . \
  --provider local \
  --pkg-storage-dir /srv/salt-repo
```

### GitHub Actions Workflow

**`.github/workflows/release.yml`:**

```yaml
name: Release Formula

on:
  push:
    branches: [main]
    paths:
      - '.saltbundle.yaml'
      - '**.sls'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Salt Bundle
        run: pip install salt-bundle

      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: |
          salt-bundle repo release \
            --formulas-dir . \
            --single \
            --provider github
```

See [CI/CD Integration](cicd-integration.md) for more examples.

### GitLab CI Pipeline

**`.gitlab-ci.yml`:**

```yaml
release:
  stage: deploy
  image: python:3.10
  script:
    - pip install salt-bundle
    - |
      salt-bundle repo release \
        --formulas-dir . \
        --single \
        --provider local \
        --pkg-storage-dir ./repo
  artifacts:
    paths:
      - repo/
  only:
    changes:
      - .saltbundle.yaml
      - "*.sls"
```

## Best Practices

### Versioning

**Follow Semantic Versioning:**

- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

**Examples:**

```yaml
# Initial release
version: 1.0.0

# Add new state file (non-breaking)
version: 1.1.0

# Fix bug in state
version: 1.1.1

# Change state structure (breaking)
version: 2.0.0
```

### Dependencies

**Declare all dependencies:**

```yaml
dependencies:
  - name: common
    version: "^1.0"    # Compatible with 1.x
  - name: firewall
    version: "~2.3"    # Compatible with 2.3.x
```

**Avoid:**
- Implicit dependencies (undeclared requirements)
- Circular dependencies

### Documentation

**Include in your formula:**

- `README.md` - Usage instructions
- `CHANGELOG.md` - Version history
- Examples in `examples/` or `pillar.example`
- Inline comments in states

### Testing

**Test before publishing:**

```bash
# 1. Test packaging
salt-bundle formula pack

# 2. Test installation in clean environment
mkdir test-project
cd test-project
salt-bundle project init

# Add local repository
salt-bundle repo add --name test --url file:///path/to/repo

# Add dependency
# .salt-dependencies.yaml:
# dependencies:
#   my-formula: "1.0.0"

# Install
salt-bundle project update

# 3. Test with Salt
salt-call --local \
  --file-root=vendor \
  state.show_sls my-formula
```

### Security

**Check package contents:**

```bash
# Before publishing, verify no sensitive data
tar -tzf my-formula-1.0.0.tgz | grep -E '\.(key|pem|password|secret)'
```

**Use `.saltbundleignore`:**

```
# Exclude sensitive files
*.key
*.pem
secrets/
.env
```

### Metadata Quality

**Good metadata helps users:**

```yaml
name: nginx
version: 2.1.0
description: Complete Nginx web server configuration with SSL support

keywords:
  - nginx
  - web-server
  - reverse-proxy
  - ssl

maintainers:
  - name: DevOps Team
    email: devops@example.com

sources:
  - https://github.com/example/salt-nginx
  - https://nginx.org/

salt:
  min_version: "3006"
  max_version: "3009"
```

## Troubleshooting

### Error: Invalid package name

**Problem:**
```
Error: Invalid package name: My-Formula
```

**Solution:** Use lowercase letters, numbers, hyphens, underscores:
```yaml
name: my-formula  # Good
name: myformula   # Good
name: my_formula  # Good
name: My-Formula  # Bad (uppercase)
name: my@formula  # Bad (special chars)
```

### Error: Invalid semver

**Problem:**
```
Error: Invalid semver version: v1.0
```

**Solution:** Use proper semver format:
```yaml
version: 1.0.0    # Good
version: 1.0      # Bad (missing patch)
version: v1.0.0   # Bad (no 'v' prefix)
```

### Error: No .sls files found

**Problem:**
```
Error: No .sls files found in formula directory
```

**Solution:** Ensure at least one `.sls` file exists:
```bash
touch init.sls
```

### Warning: Failed to process archive

**Problem:**
```
Warning: Failed to process my-formula-1.0.0.tgz: Invalid metadata
```

**Solution:** Verify `.saltbundle.yaml` is valid YAML:
```bash
python3 -c "import yaml; yaml.safe_load(open('.saltbundle.yaml'))"
```

## Next Steps

- [Repository Setup](repository-setup.md) - Set up your repository
- [Formula Configuration](formula-configuration.md) - Complete metadata reference
- [CI/CD Integration](cicd-integration.md) - Automate publishing
- [Version Constraints](version-constraints.md) - Understand semver
