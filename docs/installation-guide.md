# Formula Installation Guide

This guide explains how to use Salt Bundle to install and manage Salt formula dependencies in your projects.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setting Up a Project](#setting-up-a-project)
- [Adding Repositories](#adding-repositories)
- [Managing Dependencies](#managing-dependencies)
- [Installation Process](#installation-process)
- [Salt Integration](#salt-integration)
- [Workflows](#workflows)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Salt Bundle installed: `pip install salt-bundle`
- Salt installed (for running states)
- Access to at least one formula repository

## Setting Up a Project

### Initialize Project

```bash
# Create project directory
mkdir my-infrastructure
cd my-infrastructure

# Initialize project configuration
salt-bundle init --project
```

You'll be prompted for:
- **Project name**: Identifier for your project
- **Version**: Project version (optional)

This creates `.saltbundle.yaml`:

```yaml
project: my-infrastructure
version: 0.1.0
vendor_dir: vendor

repositories: []
dependencies: {}
```

### Project Structure

Recommended structure:

```
my-infrastructure/
├── .saltbundle.yaml    # Project configuration
├── salt-bundle.lock    # Locked dependency versions (generated)
├── salt/               # Your custom states
│   ├── top.sls
│   └── custom/
│       └── init.sls
├── pillar/             # Your pillar data
│   ├── top.sls
│   └── data.sls
└── vendor/             # Installed dependencies (generated)
    ├── nginx/
    ├── mysql/
    └── redis/
```

## Adding Repositories

### Global Repositories

Add repositories to your user configuration (`~/.config/salt-bundle/config.yaml`):

```bash
# Add public repository
salt-bundle add-repo \
  --name saltstack \
  --url https://salt-formulas.saltstack.com/

# Add private repository
salt-bundle add-repo \
  --name company \
  --url https://formulas.company.com/

# Add local repository
salt-bundle add-repo \
  --name local \
  --url file:///srv/salt-repo/
```

**View configuration:**

```bash
cat ~/.config/salt-bundle/config.yaml
```

```yaml
repositories:
  - name: saltstack
    url: https://salt-formulas.saltstack.com/
  - name: company
    url: https://formulas.company.com/
  - name: local
    url: file:///srv/salt-repo/
```

### Project-Specific Repositories

Add repositories directly in `.saltbundle.yaml`:

```yaml
project: my-infrastructure
version: 0.1.0
vendor_dir: vendor

repositories:
  - name: main
    url: https://salt-repo.example.com/
  - name: testing
    url: https://test-repo.example.com/

dependencies: {}
```

**Priority:** Project repositories are checked first, then global repositories.

## Managing Dependencies

### Add Dependencies

Edit `.saltbundle.yaml`:

```yaml
project: my-infrastructure
version: 0.1.0
vendor_dir: vendor

repositories:
  - name: main
    url: https://salt-repo.example.com/

dependencies:
  # Latest compatible with 2.x
  nginx: "^2.0.0"

  # Latest compatible with 5.7.x
  mysql: "~5.7"

  # Exact version
  redis: "6.2.1"

  # Version range
  postgresql: ">=12.0,<14.0"

  # From specific repository
  main/internal-app: "^1.0"
```

See [Version Constraints](version-constraints.md) for details on version formats.

### Repository-Specific Dependencies

Use `repository/package` format to pull from specific repository:

```yaml
dependencies:
  # Search all repositories
  nginx: "^2.0.0"

  # Only from 'company' repository
  company/internal-formula: "^1.0.0"

  # Only from 'testing' repository
  testing/experimental: "^0.1.0"
```

## Installation Process

### Install Dependencies

```bash
cd my-infrastructure
salt-bundle install
```

**What happens:**

1. **Dependency Resolution**
   - Reads `.saltbundle.yaml`
   - Fetches repository indexes
   - Resolves versions matching constraints
   - Creates/updates `salt-bundle.lock`

2. **Package Download**
   - Downloads packages (with caching)
   - Verifies SHA256 checksums
   - Stores in `~/.cache/salt-bundle/packages/`

3. **Installation**
   - Extracts packages to `vendor/` directory
   - Each formula in its own subdirectory

**Output example:**

```
Resolving dependencies...
Resolving nginx...
  ✓ nginx 2.1.5 from main
Resolving mysql...
  ✓ mysql 5.7.8 from main
Resolving redis...
  ✓ redis 6.2.1 from main

Installing nginx 2.1.5...
Installing mysql 5.7.8...
Installing redis 6.2.1...

Installation complete!
```

### Lock File

After installation, `salt-bundle.lock` is created:

```yaml
dependencies:
  nginx:
    version: 2.1.5
    repository: main
    url: https://salt-repo.example.com/nginx-2.1.5.tgz
    digest: sha256:abc123...
  mysql:
    version: 5.7.8
    repository: main
    url: https://salt-repo.example.com/mysql-5.7.8.tgz
    digest: sha256:def456...
  redis:
    version: 6.2.1
    repository: main
    url: https://salt-repo.example.com/redis-6.2.1.tgz
    digest: sha256:ghi789...
```

**Commit this file** to ensure reproducible deployments.

### Install from Lock File

When `salt-bundle.lock` exists:

```bash
# Install exact versions from lock file
salt-bundle install

# Or explicitly
salt-bundle vendor
```

This installs exactly the versions in the lock file without resolving.

### Update Dependencies

Update to latest compatible versions:

```bash
# Update all dependencies
salt-bundle install --update-lock

# Check what would be updated (planned feature)
# salt-bundle update --dry-run

# Update single dependency (planned feature)
# salt-bundle update --dependency nginx
```

### Ignore Lock File

Resolve from scratch (not recommended for production):

```bash
salt-bundle install --no-lock
```

## Salt Integration

### Method 1: Automatic Salt Loader Plugin (Recommended)

After installing `salt-bundle` via pip, Salt automatically discovers formulas without any configuration changes.

**Installation:**

```bash
pip install salt-bundle
```

**Usage:**

Simply run Salt commands from your project directory:

```bash
cd my-infrastructure

# Formulas automatically discovered from vendor/
salt-call state.apply nginx

# Works with salt-ssh too
salt-ssh '*' state.apply mysql

# Check discovered formulas
salt-call pillar.get saltbundle:formulas

# Verify file_roots includes vendor/
salt-call config.get file_roots
```

**How it works:**

1. After `pip install salt-bundle`, Salt automatically loads the plugin via entry points
2. Plugin searches for `.saltbundle.yaml` in current working directory (or parent directories)
3. Reads `vendor_dir` from config (defaults to `vendor`)
4. Automatically adds all formulas from `vendor/` to Salt's `file_roots`
5. No changes to `/etc/salt/master` or `/etc/salt/minion` required!

**Requirements:**

- `.saltbundle.yaml` must exist in current directory or parent directories
- `vendor_dir` must be specified in config (defaults to `vendor`)
- Formulas must be installed via `salt-bundle install` or `salt-bundle vendor`

**Verification:**

```bash
# Check if loader is working - should show project info
salt-call pillar.get saltbundle

# Example output:
# saltbundle:
#   project_dir: /path/to/my-infrastructure
#   vendor_dir: vendor
#   formulas:
#     - nginx
#     - mysql
#     - redis
#   formula_paths:
#     - /path/to/my-infrastructure/vendor/nginx
#     - /path/to/my-infrastructure/vendor/mysql
#     - /path/to/my-infrastructure/vendor/redis
```

See [Automatic Loader Examples](../examples/project/README.md) for more details.

### Method 2: Wrapper Script

Create `salt.sh` in project root:

```bash
#!/usr/bin/env bash
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENDOR_DIR="${PROJECT_ROOT}/vendor"
SALT_DIR="${PROJECT_ROOT}/salt"
PILLAR_DIR="${PROJECT_ROOT}/pillar"

exec salt-call --local \
  --file-root="${SALT_DIR}:${VENDOR_DIR}" \
  --pillar-root="${PILLAR_DIR}" \
  "$@"
```

Make executable:

```bash
chmod +x salt.sh
```

**Usage:**

```bash
# Apply all states
./salt.sh state.apply

# Apply specific state from vendor
./salt.sh state.apply nginx

# Apply your custom state
./salt.sh state.apply custom

# Show SLS from vendor
./salt.sh state.show_sls nginx
```

### Method 3: Master Configuration

For permanent configuration, edit `/etc/salt/master`:

```yaml
file_roots:
  base:
    - /srv/salt
    - /srv/my-infrastructure/vendor

pillar_roots:
  base:
    - /srv/pillar
```

Restart master:

```bash
systemctl restart salt-master
```

**Note:** With the automatic loader plugin (Method 1), this configuration is not necessary.

### Method 4: Minion Configuration

For permanent configuration, edit `/etc/salt/minion`:

```yaml
file_roots:
  base:
    - /srv/salt
    - /srv/my-infrastructure/vendor

pillar_roots:
  base:
    - /srv/pillar
```

Restart minion:

```bash
systemctl restart salt-minion
```

**Note:** With the automatic loader plugin (Method 1), this configuration is not necessary.

### Using Formulas

**top.sls:**

```yaml
base:
  '*':
    - nginx           # From vendor/nginx/
    - mysql           # From vendor/mysql/
    - custom.myapp    # From salt/custom/myapp.sls
```

**Command line:**

```bash
# Apply nginx formula
salt '*' state.apply nginx

# Or with wrapper
./salt.sh state.apply nginx
```

## Workflows

### Development Workflow

```bash
# 1. Start new project
mkdir my-project
cd my-project
salt-bundle init --project

# 2. Add repositories
salt-bundle add-repo --name main --url https://formulas.example.com/

# 3. Add dependencies
cat >> .saltbundle.yaml << EOF
dependencies:
  nginx: "^2.0"
  mysql: "^5.7"
EOF

# 4. Install
salt-bundle install

# 5. Test
./salt.sh state.show_sls nginx

# 6. Commit
git add .saltbundle.yaml salt-bundle.lock
git commit -m "Add nginx and mysql dependencies"
```

### Production Deployment

```bash
# 1. Clone project
git clone https://github.com/company/infrastructure.git
cd infrastructure

# 2. Install dependencies from lock file
salt-bundle vendor

# 3. Verify integrity
salt-bundle verify

# 4. Apply states
./salt.sh state.apply
```

### Update Workflow

```bash
# 1. Check current versions
cat salt-bundle.lock

# 2. Update dependencies
salt-bundle install --update-lock

# 3. Test new versions
./salt.sh state.apply test=True

# 4. Commit if successful
git add salt-bundle.lock
git commit -m "Update dependencies"
```

### Adding New Dependency

```bash
# 1. Edit configuration
cat >> .saltbundle.yaml << EOF
  redis: "^6.0"
EOF

# 2. Install
salt-bundle install

# 3. Test
./salt.sh state.show_sls redis

# 4. Use in states
cat > salt/app.sls << EOF
include:
  - redis

app-depends-on-redis:
  test.succeed_without_changes:
    - require:
      - sls: redis
EOF

# 5. Commit
git add .saltbundle.yaml salt-bundle.lock salt/app.sls
git commit -m "Add redis dependency"
```

## Verification

### Verify Dependencies

Check that all dependencies are correctly installed:

```bash
salt-bundle verify
```

**Output:**

```
✓ nginx 2.1.5
✓ mysql 5.7.8
✓ redis 6.2.1

All dependencies verified successfully!
```

**Errors detected:**

```
✓ nginx 2.1.5
  mysql: not installed
✓ redis 6.2.1

Errors found:
  mysql: not installed
```

### Manual Verification

```bash
# Check vendor directory
ls -la vendor/

# Check formula contents
ls -la vendor/nginx/

# Verify metadata
cat vendor/nginx/.saltbundle.yaml

# Test with Salt
./salt.sh state.show_sls nginx
```

## Caching

### Cache Location

```bash
~/.cache/salt-bundle/
├── index/        # Repository indexes
└── packages/     # Downloaded packages
```

### Clear Cache

```bash
# Remove all cache
rm -rf ~/.cache/salt-bundle/

# Remove package cache only
rm -rf ~/.cache/salt-bundle/packages/

# Remove index cache only
rm -rf ~/.cache/salt-bundle/index/
```

## Troubleshooting

### Error: .saltbundle.yaml not found

**Problem:**
```
Error: .saltbundle.yaml not found. Run 'salt-bundle init --project' first.
```

**Solution:**
```bash
salt-bundle init --project
```

### Error: No repositories configured

**Problem:**
```
Warning: No repositories configured
```

**Solution:** Add at least one repository:
```bash
salt-bundle add-repo --name main --url https://formulas.example.com/
```

Or add to `.saltbundle.yaml`:
```yaml
repositories:
  - name: main
    url: https://formulas.example.com/
```

### Error: Repository not found

**Problem:**
```
Error: Repository 'main' not found for dependency 'main/nginx'
Available repositories: saltstack, company
```

**Solution:** Add the repository:
```bash
salt-bundle add-repo --name main --url https://repo.example.com/
```

Or remove repository prefix from dependency:
```yaml
dependencies:
  nginx: "^2.0"  # Instead of main/nginx
```

### Error: Could not resolve dependency

**Problem:**
```
Error: Could not resolve dependency: nginx ^2.0.0
```

**Solutions:**

1. Check package exists in repository:
```bash
# Download index manually
curl https://repo.example.com/index.yaml
```

2. Check version constraint:
```yaml
# Try broader constraint
nginx: "^1.0"  # Instead of ^2.0
```

3. Check repository URL:
```bash
salt-bundle add-repo --name main --url https://correct-url.example.com/
```

### Error: Digest mismatch

**Problem:**
```
Error: Digest mismatch for nginx-2.1.5.tgz
```

**Solutions:**

1. Clear cache and retry:
```bash
rm -rf ~/.cache/salt-bundle/packages/
salt-bundle install
```

2. Check repository integrity:
```bash
# Re-generate index on repository server
cd /srv/salt-repo
salt-bundle index
```

### Error: Network timeout

**Problem:**
```
Error: Failed to fetch from main: timeout
```

**Solutions:**

1. Check network connectivity:
```bash
curl -I https://repo.example.com/index.yaml
```

2. Use local repository:
```bash
salt-bundle add-repo --name local --url file:///srv/salt-repo/
```

### Vendor directory not found

**Problem:** Salt can't find formulas from vendor directory

**Solution:** Check `file_roots` configuration:

```bash
# Test with wrapper script
./salt.sh --file-root=./vendor state.show_sls nginx

# Or verify file_roots in config
salt-call --local config.get file_roots
```

## Next Steps

- [Project Configuration](project-configuration.md) - Complete `.saltbundle.yaml` reference
- [Version Constraints](version-constraints.md) - Understanding semver
- [CLI Reference](cli-reference.md) - All commands
- [Publishing Guide](publishing-guide.md) - Create your own formulas
