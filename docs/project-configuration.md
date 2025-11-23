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
```

**Repository object fields:**
- `name` (required): Repository identifier
- `url` (required): Repository base URL (HTTP/HTTPS/file)

**Priority order:**
1. Project repositories (top to bottom)
2. Global user repositories (top to bottom)

See [Adding Repositories](installation-guide.md#adding-repositories) for details.

#### `dependencies`

**Type:** Dictionary (string → string)
**Default:** Empty dictionary

Formula dependencies with version constraints.

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

### salt-bundle.lock

After running `salt-bundle install`, a lock file is generated:

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

**Always commit this file** to version control for reproducible deployments.

### Vendor Directory

Structure after installation:

```
vendor/
├── nginx/
│   ├── .saltbundle.yaml
│   ├── init.sls
│   └── ...
├── mysql/
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
salt-bundle install

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
salt-bundle.lock           # Locked versions
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
salt-bundle install

# Verify installation
salt-bundle verify

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
salt-bundle init --project

# Add dependencies
cat >> .salt-dependencies.yaml << EOF
dependencies:
  nginx: "^2.0.0"
EOF

# Install
salt-bundle install
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
salt-bundle install
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

## Troubleshooting

See [Installation Guide - Troubleshooting](installation-guide.md#troubleshooting) for common issues.

## Next Steps

- [Installation Guide](installation-guide.md) - Installing dependencies
- [Version Constraints](version-constraints.md) - Understanding constraints
- [Formula Configuration](formula-configuration.md) - Creating formulas
- [Repository Setup](repository-setup.md) - Setting up repositories
