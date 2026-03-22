# Project Configuration Reference

Complete reference for `.salt-dependencies.yaml` configuration in project directories.

## Overview

The `.salt-dependencies.yaml` file in a Salt project directory defines project metadata, repositories, and dependencies for formula management.

## Basic Structure

File: `.salt-dependencies.yaml` (in Salt project root)

```yaml
project: my-infrastructure
version: 0.1.0
vendor_dir: vendor

repositories:
  - name: main
    url: https://formulas.example.com/
  - name: internal
    url: https://internal.example.com/

dependencies:
  nginx: "^2.0.0"
  mysql: "~5.7"
  internal/app: "^1.0.0"
```

## Fields Reference

### Required Fields

#### `project`

**Type:** String
**Required:** Yes

Project identifier. Used for reference, doesn't need to follow strict naming rules.

```yaml
project: my-infrastructure
project: prod-servers
project: Company Infrastructure
```

### Optional Fields

#### `version`

**Type:** String
**Default:** None

Project version. Useful for tracking infrastructure versions.

```yaml
version: 0.1.0
version: 2.3.1
version: 2024.01.15
```

#### `vendor_dir`

**Type:** String
**Default:** `"vendor"`

Directory where formula dependencies will be installed, relative to project root.

```yaml
vendor_dir: vendor        # Default
vendor_dir: formulas      # Custom
vendor_dir: lib/formulas  # Nested
```

**Recommended:** Keep default `vendor` for consistency.

#### `repositories`

**Type:** List of objects
**Default:** Empty list

Project-specific repositories. These are checked **before** global user repositories.

```yaml
repositories:
  - name: main
    url: https://salt-formulas.example.com/
  - name: testing
    url: https://test.example.com/repo/
  - name: local
    url: file:///srv/salt-repo/
  - name: my-formula
    type: path
    url: ../my-formula
```

**Repository object fields:**
- `name` (required): Repository identifier
- `url` (required): Repository base URL (HTTP/HTTPS/file) or local directory path for `type: path`
- `type` (optional): Repository type — `remote` (default) or `path`

**`type: path` repositories** point directly to a local formula directory and are intended for development and testing. Instead of downloading a `.tgz` archive, salt-bundle creates a symlink from `vendor/<name>` to the local directory. Changes made in the local directory are immediately visible without repacking or republishing. See [Path Repositories](#path-repositories-for-local-development) for details.

**Priority order:**
1. Project repositories (top to bottom)
2. Global user repositories (top to bottom)

See [Adding Repositories](installation-guide.md#adding-repositories) for details.

#### `dependencies`

**Type:** Dictionary (string → string)
**Default:** Empty dictionary

Formula dependencies with version constraints. These dependencies are **transitive**. When you run `salt-bundle project update`, it will:
1.  Read these direct dependencies.
2.  Pull in all transitive dependencies (dependencies of dependencies) from the formulas' `.saltbundle.yaml` files.
3.  Resolve the entire dependency tree.
4.  Install all resolved formulas into the `vendor_dir`.

**Format:**

```yaml
dependencies:
  # package-name: version-constraint
  nginx: "^2.0.0"

  # repo-name/package-name: version-constraint
  main/mysql: "~5.7"
```

**Simple dependencies** (search all repositories):

```yaml
dependencies:
  nginx: "^2.0.0"
  mysql: "~5.7.8"
  redis: ">=6.0,<7.0"
```

**Repository-specific dependencies** (format: `repo/package`):

```yaml
dependencies:
  main/nginx: "^2.0.0"          # Only from 'main' repo
  testing/experimental: "^0.1"   # Only from 'testing' repo
```

**Mixed dependencies:**

```yaml
dependencies:
  nginx: "^2.0.0"                # Search all repos
  mysql: "~5.7"                  # Search all repos
  internal/app: "^1.0.0"         # Only from 'internal' repo
```

See [Version Constraints](version-constraints.md) for constraint formats.

## Complete Examples

### Minimal Project

```yaml
project: my-project
```

### Simple Project

```yaml
project: web-infrastructure
version: 1.0.0

repositories:
  - name: saltstack
    url: https://formulas.saltstack.com/

dependencies:
  nginx: "^2.0.0"
  mysql: "^5.7"
  redis: "^6.0"
```

### Production Project

```yaml
project: production-infrastructure
version: 2.3.0
vendor_dir: vendor

repositories:
  - name: main
    url: https://salt-formulas.example.com/
  - name: company
    url: https://internal.example.com/formulas/
  - name: backup
    url: https://backup-repo.example.com/

dependencies:
  # Web tier
  nginx: "^2.1.0"
  haproxy: "~1.8"

  # Application tier
  company/application: "^3.2.0"
  python: "^3.9"
  nodejs: "^16.0"

  # Data tier
  postgresql: "^13.0"
  redis: "^6.2"
  elasticsearch: "~7.10"

  # Infrastructure
  common: "^2.0"
  firewall: "~1.5"
  monitoring: "^4.0"
  logging: "^2.1"
```

### Development Project

```yaml
project: dev-environment
version: 0.1.0
vendor_dir: vendor

repositories:
  - name: testing
    url: https://test-repo.example.com/
  - name: main
    url: https://prod-repo.example.com/

dependencies:
  # Use testing versions
  testing/nginx: "^2.0.0-beta"
  testing/app: "^1.0.0-rc.1"

  # Use stable versions for critical components
  postgresql: "13.5.0"
  redis: "6.2.6"
```

### Development Project with Local Formulas

When actively developing a formula, use `type: path` to reference it directly without packaging:

```yaml
project: dev-environment
version: 0.1.0
vendor_dir: vendor

repositories:
  # Local formula under active development — no packaging needed
  - name: my-nginx
    type: path
    url: ../nginx-formula

  # Remote repository for stable dependencies
  - name: main
    url: https://formulas.example.com/

dependencies:
  nginx: "^2.0.0"       # resolved from local path repo
  postgresql: "^13.0"   # resolved from main remote repo
```

Running `salt-bundle project update` will create a symlink `vendor/nginx -> /abs/path/to/nginx-formula`. Any edit to the formula is immediately available without re-running any commands.

### Multi-Environment Project

```yaml
project: multi-env-infrastructure
version: 1.0.0
vendor_dir: vendor

repositories:
  - name: prod
    url: https://prod-formulas.example.com/
  - name: staging
    url: https://staging-formulas.example.com/
  - name: common
    url: https://common-formulas.example.com/

dependencies:
  # Environment-specific
  prod/app: "^2.0.0"

  # Common dependencies
  common/nginx: "^2.1.0"
  common/monitoring: "^1.5.0"
```

## Repository Configuration

### Global vs Project Repositories

**Global repositories** (`~/.config/salt-bundle/config.yaml`):
```yaml
repositories:
  - name: public
    url: https://public-formulas.example.com/
  - name: community
    url: https://community.example.com/
```

**Project repositories** (`.salt-dependencies.yaml`):
```yaml
repositories:
  - name: company
    url: https://internal.example.com/
```

**Resolution order:**
1. Project `company` repository
2. Global `public` repository
3. Global `community` repository

### Repository URL Formats

**HTTPS:**
```yaml
repositories:
  - name: main
    url: https://formulas.example.com/
  - name: cdn
    url: https://cdn.example.com/salt/
```

**HTTP:**
```yaml
repositories:
  - name: local
    url: http://localhost:8080/
```

**File (local filesystem):**
```yaml
repositories:
  - name: local
    url: file:///srv/salt-repo/
  - name: dev
    url: file:///home/user/formulas/repo/
```

**Important:** Always include trailing slash for URLs.

## Dependency Configuration

### Version Constraint Formats

See [Version Constraints](version-constraints.md) for detailed information.

**Summary:**

```yaml
dependencies:
  # Exact version
  nginx: "2.1.5"

  # Caret (compatible)
  mysql: "^5.7.0"       # >=5.7.0, <6.0.0

  # Tilde (patch-level)
  redis: "~6.2.0"       # >=6.2.0, <6.3.0

  # Wildcard
  postgresql: "13.*"    # Any 13.x.x

  # Range
  memcached: ">=1.6,<2.0"

  # Repository-specific
  main/app: "^1.0.0"
```

### Common Patterns

**Flexible (recommended for development):**

```yaml
dependencies:
  nginx: "^2.0.0"    # Latest 2.x
  mysql: "^5.7"      # Latest 5.x
  redis: "^6.0"      # Latest 6.x
```

**Conservative (recommended for production):**

```yaml
dependencies:
  nginx: "~2.1.5"    # Only patch updates
  mysql: "~5.7.8"    # Only patch updates
  redis: "6.2.6"     # Exact version
```

**Mixed (realistic):**

```yaml
dependencies:
  # Critical: exact versions
  payment-system: "3.2.1"
  security-lib: "2.5.3"

  # Important: patch updates only
  nginx: "~2.1.5"
  postgresql: "~13.5"

  # Less critical: minor updates allowed
  logging: "^2.0"
  monitoring: "^1.5"
```

## Generated Files

### .salt-dependencies.lock

After running `salt-bundle project update`, a lock file is generated:

```yaml
dependencies:
  nginx:
    version: 2.1.5
    repository: main
    url: https://repo.example.com/nginx-2.1.5.tgz
    digest: sha256:abc123...
  mysql:
    version: 5.7.8
    repository: main
    url: https://repo.example.com/mysql-5.7.8.tgz
    digest: sha256:def456...
```

For `type: path` repositories the lock entry looks different — it records the absolute local path and uses `"path"` as the digest value:

```yaml
dependencies:
  nginx:
    version: 2.0.0
    repository: my-nginx
    url: /home/user/nginx-formula
    digest: path
    path: /home/user/nginx-formula
```

**Always commit this file** to version control for reproducible deployments.

> **Note:** Lock entries with `digest: path` reference an absolute path on the developer's machine. These entries are only useful locally — on CI/CD or other machines the path will not exist. Consider using path repositories only in developer-local overrides and keeping CI configs pointing to remote repositories.

### Vendor Directory

Structure after installation:

```
vendor/
├── nginx/          # symlink → /home/user/nginx-formula  (path repo)
├── mysql/          # unpacked directory                  (remote repo)
│   ├── .saltbundle.yaml
│   ├── init.sls
│   └── ...
└── redis/
    ├── .saltbundle.yaml
    ├── init.sls
    └── ...
```

**Don't commit** this directory (add to `.gitignore`).

## Validation

### Validate Configuration

```bash
# Try to install (validates config)
salt-bundle project install

# Or use Python
python3 << 'EOF'
import yaml
from salt_bundle.models.config_models import ProjectConfig

with open('.salt-dependencies.yaml') as f:
    data = yaml.safe_load(f)
    config = ProjectConfig(**data)
    print(f"Valid: {config.project}")
EOF
```

### Common Errors

#### Missing project field

```yaml
# Error
version: 1.0.0
dependencies:
  nginx: "^2.0"

# Fix
project: my-project
version: 1.0.0
dependencies:
  nginx: "^2.0"
```

#### Invalid repository format

```yaml
# Error
repositories:
  - main: https://example.com/

# Fix
repositories:
  - name: main
    url: https://example.com/
```

#### Invalid dependency format

```yaml
# Error (list instead of dict)
dependencies:
  - nginx: "^2.0"

# Fix
dependencies:
  nginx: "^2.0"
```

## Best Practices

### Version Control

**Commit these files:**
```
.salt-dependencies.yaml    # Project configuration
.salt-dependencies.lock           # Locked versions
```

**Don't commit:**
```
vendor/             # Installed formulas
```

**Example `.gitignore`:**
```
vendor/
.cache/
```

### Vendor Directory

- Keep default `vendor` name for consistency
- Don't modify installed formulas
- Reinstall if vendor directory is corrupted

### Repository Management

**Use descriptive names:**
```yaml
repositories:
  - name: production     # Good
  - name: company-internal  # Good
  - name: repo1          # Bad
```

**Order by priority:**
```yaml
repositories:
  - name: high-priority
    url: https://priority.example.com/
  - name: fallback
    url: https://backup.example.com/
```

### Dependencies

**Group logically:**
```yaml
dependencies:
  # Web tier
  nginx: "^2.0"
  haproxy: "^1.8"

  # Data tier
  postgresql: "^13.0"
  redis: "^6.0"

  # Monitoring
  prometheus: "^2.0"
  grafana: "^8.0"
```

**Document non-obvious dependencies:**
```yaml
dependencies:
  # Required for SSL certificate management
  certbot: "^1.0"

  # Company-specific application
  company/internal-app: "^2.0"
```

### Testing

**Test before committing:**

```bash
# Install in clean state
rm -rf vendor/
salt-bundle project install

# Verify installation
salt-bundle formula verify

# Test with Salt
salt-call --local --file-root=vendor state.show_sls nginx
```

## Migration

### From Requirements File

If you have a requirements file:

```
# requirements.txt
nginx>=2.0.0
mysql~=5.7.0
redis==6.2.1
```

Convert to `.salt-dependencies.yaml`:

```yaml
project: my-project

dependencies:
  nginx: ">=2.0.0"
  mysql: "~5.7.0"
  redis: "6.2.1"
```

### From Git Submodules

If using git submodules:

```bash
# Remove submodules
git submodule deinit -f formulas/nginx
git rm -f formulas/nginx
rm -rf .git/modules/formulas/nginx

# Create .salt-dependencies.yaml
salt-bundle project init

# Add dependencies
cat >> .salt-dependencies.yaml << EOF
dependencies:
  nginx: "^2.0.0"
EOF

# Install
salt-bundle project install
```

## Environment-Specific Configuration

### Option 1: Multiple Files

```
.salt-dependencies.yaml           # Default/dev
.salt-dependencies.prod.yaml      # Production
.salt-dependencies.staging.yaml   # Staging
```

**Install specific environment:**
```bash
cp .salt-dependencies.prod.yaml .salt-dependencies.yaml
salt-bundle project install
```

### Option 2: Override with Repository Priority

```yaml
# .salt-dependencies.yaml
project: my-app
repositories:
  - name: env-specific
    url: ${ENV_REPO_URL}  # Set via environment variable
  - name: common
    url: https://common.example.com/

dependencies:
  app: "^1.0"  # Resolves from env-specific first
```

## Path Repositories for Local Development

Path repositories allow you to use a local formula directory as a dependency source. This is the recommended workflow when you are simultaneously developing a formula and a project that uses it.

### How It Works

1. You add a repository with `type: path` pointing to your local formula directory.
2. `salt-bundle project update` reads `.saltbundle.yaml` from that directory, resolves the version constraint, and creates a **symlink** in `vendor/` instead of downloading an archive.
3. Any changes you make to the local formula are immediately reflected in the vendor directory — no repacking required.

### Workflow Example

Suppose you have this directory layout:

```
~/projects/
├── nginx-formula/          # formula under development
│   ├── .saltbundle.yaml    # name: nginx, version: 2.1.0
│   ├── init.sls
│   └── ...
└── my-infra/               # Salt project using the formula
    ├── .salt-dependencies.yaml
    └── top.sls
```

Configure `.salt-dependencies.yaml` in `my-infra/`:

```yaml
project: my-infra

repositories:
  - name: local-nginx
    type: path
    url: ../nginx-formula   # relative path from the project directory

  - name: main
    url: https://formulas.example.com/

dependencies:
  nginx: "^2.0.0"
```

Run:

```bash
cd ~/projects/my-infra
salt-bundle project update
```

Result:

```
Resolving nginx...
  ✓ nginx 2.1.0 from local-nginx
Installing nginx 2.1.0...
  (symlinked from /home/user/projects/nginx-formula)
```

`vendor/nginx` is now a symlink to `~/projects/nginx-formula`. Edit the formula, test immediately:

```bash
salt-call --local state.apply nginx
```

### Switching Between Local and Remote

When your formula is ready and published to a remote repository, remove the `path` repository entry and run `salt-bundle project update` again — the symlink will be replaced with the downloaded archive.

```yaml
# Before (development)
repositories:
  - name: local-nginx
    type: path
    url: ../nginx-formula

# After (production)
repositories:
  - name: main
    url: https://formulas.example.com/
```

### Relative vs Absolute Paths

Both relative and absolute paths are supported in `url`:

```yaml
repositories:
  # Relative (resolved from the project directory)
  - name: formula-a
    type: path
    url: ../formula-a

  # Absolute
  - name: formula-b
    type: path
    url: /home/user/projects/formula-b
```

Relative paths are converted to absolute internally when the lock file is written.

### Limitations

- The local formula directory **must contain** a valid `.saltbundle.yaml` with `name` and `version`.
- The version in `.saltbundle.yaml` must satisfy the constraint in `dependencies`, otherwise resolution fails.
- Lock file entries with `digest: path` contain an **absolute path** specific to the developer's machine. Do not rely on them in CI/CD environments — use remote repository entries there instead.
- `type: path` is not supported in global user config (`~/.config/salt-bundle/config.yaml`) because paths are project-relative. Declare them in the project's `.salt-dependencies.yaml`.

## Troubleshooting

See [Installation Guide - Troubleshooting](installation-guide.md#troubleshooting) for common issues.

## Next Steps

- [Installation Guide](installation-guide.md) - Installing dependencies
- [Version Constraints](version-constraints.md) - Understanding constraints
- [Formula Configuration](formula-configuration.md) - Creating formulas
- [Repository Setup](repository-setup.md) - Setting up repositories
