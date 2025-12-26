# File Formats Reference

Complete reference for all Salt Bundle file formats.

## Overview

Salt Bundle uses YAML for all configuration and data files:

| File                      | Location                 | Purpose                    |
|---------------------------|--------------------------|----------------------------|
| `.saltbundle.yaml`        | Formula root             | Formula metadata           |
| `.salt-dependencies.yaml` | Project root             | Project configuration      |
| `.salt-dependencies.lock` | Project root             | Locked dependency versions |
| `index.yaml`              | Repository root          | Package index              |
| `config.yaml`             | `~/.config/salt-bundle/` | User global configuration  |

## Formula Metadata (.saltbundle.yaml)

### Location

Formula root directory.

### Format

```yaml
name: string                    # Required: Package name (^[a-z0-9_-]+$)
version: string                 # Required: Semantic version (MAJOR.MINOR.PATCH)
description: string             # Optional: Short description
keywords: [string, ...]         # Optional: List of tags
sources: [string, ...]          # Optional: List of URLs
maintainers:                    # Optional: List of maintainers
  - name: string                # Required: Maintainer name
    email: string               # Optional: Contact email
salt:                           # Optional: Salt compatibility
  min_version: string           # Optional: Minimum Salt version
  max_version: string           # Optional: Maximum Salt version
dependencies:                   # Optional: Formula dependencies
  - name: string                # Required: Dependency name
    version: string             # Required: Version constraint
entry:                          # Optional: Entry points (reserved)
  states_root: string           # Default: "."
  pillar_root: string           # Optional
  modules: [string, ...]        # Optional: Custom module directories
```

### Example

```yaml
name: nginx
version: 2.1.5
description: Nginx web server with SSL support

keywords:
  - nginx
  - webserver
  - ssl

sources:
  - https://github.com/example/nginx-formula
  - https://nginx.org/

maintainers:
  - name: DevOps Team
    email: devops@example.com

salt:
  min_version: "3006"
  max_version: "3009"

dependencies:
  - name: common
    version: "^1.0.0"
  - name: firewall
    version: "~2.3.0"
```

### Validation Rules

**name:**
- Pattern: `^[a-z0-9_-]+$`
- Only lowercase letters, numbers, hyphens, underscores
- Examples: `nginx`, `my-formula`, `app_config`

**version:**
- Pattern: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`
- Must follow semantic versioning
- Examples: `1.0.0`, `2.1.3-beta.1`, `1.0.0+build123`

**salt.min_version / salt.max_version:**
- Salt version numbers: `3006`, `3007`, `3008`, `3009`
- Or full versions: `3006.0`, `3007.1`

**dependencies[].version:**
- Version constraint string
- Examples: `^1.0.0`, `~2.3.1`, `>=1.0,<2.0`
- See [Version Constraints](version-constraints.md)

## Project Configuration (.salt-dependencies.yaml)

### Location

Project root directory (Salt projects).

### Format

```yaml
project: string                 # Required: Project name
version: string                 # Optional: Project version
vendor_dir: string              # Optional: Vendor directory (default: "vendor")
repositories:                   # Optional: Project-specific repositories
  - name: string                # Required: Repository name
    url: string                 # Required: Repository URL
dependencies:                   # Optional: Formula dependencies
  package-name: version-constraint
  repo-name/package-name: version-constraint
```

### Example

```yaml
project: my-infrastructure
version: 1.2.0
vendor_dir: vendor

repositories:
  - name: main
    url: https://salt-formulas.example.com/
  - name: internal
    url: https://internal.example.com/formulas/
  - name: local
    url: file:///srv/salt-repo/

dependencies:
  # Simple dependencies (search all repos)
  nginx: "^2.0.0"
  mysql: "~5.7.8"
  redis: ">=6.0,<7.0"

  # Repository-specific dependencies
  main/postgresql: "^13.0"
  internal/app: "^1.0.0"
  local/testing: "^0.1.0"
```

### Validation Rules

**project:**
- Any string (no strict pattern)
- Used for identification only

**vendor_dir:**
- Relative path from project root
- Default: `"vendor"`

**repositories[].url:**
- Valid URL: HTTP, HTTPS, or file://
- Must end with `/` for best compatibility
- Examples:
  - `https://example.com/repo/`
  - `http://localhost:8080/`
  - `file:///srv/salt-repo/`

**dependencies:**
- Dictionary format: `name: constraint`
- Name format: `package` or `repo/package`
- Constraint: version constraint string

## Lock File (.salt-dependencies.lock)

### Location

Project root directory (auto-generated).

### Format

```yaml
dependencies:
  package-name:
    version: string             # Exact version
    repository: string          # Repository name
    url: string                 # Package URL
    digest: string              # SHA256 digest (sha256:hex)
```

### Example

```yaml
dependencies:
  nginx:
    version: 2.1.5
    repository: main
    url: https://salt-formulas.example.com/nginx-2.1.5.tgz
    digest: sha256:abc123def456...

  mysql:
    version: 5.7.8
    repository: main
    url: https://salt-formulas.example.com/mysql-5.7.8.tgz
    digest: sha256:789012ghi345...

  redis:
    version: 6.2.6
    repository: local
    url: file:///srv/salt-repo/redis-6.2.6.tgz
    digest: sha256:456789jkl012...
```

### Properties

**Generated by:** `salt-bundle project install`

**Purpose:**
- Lock exact versions for reproducibility
- Store package URLs and checksums
- Enable offline/cached installation

**Version Control:**
- **Should commit:** Yes (for reproducible deployments)
- **Should edit:** No (auto-generated)

**digest format:**
- Format: `sha256:<64-character hex>`
- Used for integrity verification

## Repository Index (index.yaml)

### Location

Repository root directory.

### Format

```yaml
apiVersion: string              # Always "v1"
generated: datetime             # ISO 8601 timestamp
packages:
  package-name:                 # Package name
    - version: string           # Semantic version
      url: string               # Package URL (absolute or relative)
      digest: string            # SHA256 digest
      created: datetime         # ISO 8601 timestamp
      keywords: [string, ...]   # Tags from formula metadata
      maintainers:              # From formula metadata
        - name: string
          email: string
      sources: [string, ...]    # From formula metadata
```

### Example

```yaml
apiVersion: v1
generated: "2025-01-15T10:30:00Z"

packages:
  nginx:
    - version: 2.1.5
      url: https://repo.example.com/nginx-2.1.5.tgz
      digest: sha256:abc123def456...
      created: "2025-01-15T09:00:00Z"
      keywords:
        - nginx
        - webserver
        - ssl
      maintainers:
        - name: DevOps Team
          email: devops@example.com
      sources:
        - https://github.com/example/nginx-formula

    - version: 2.1.0
      url: https://repo.example.com/nginx-2.1.0.tgz
      digest: sha256:def456ghi789...
      created: "2025-01-10T08:00:00Z"
      keywords:
        - nginx
        - webserver
      maintainers:
        - name: DevOps Team
          email: devops@example.com
      sources:
        - https://github.com/example/nginx-formula

  mysql:
    - version: 5.7.8
      url: https://repo.example.com/mysql-5.7.8.tgz
      digest: sha256:ghi789jkl012...
      created: "2025-01-12T10:00:00Z"
      keywords:
        - mysql
        - database
      maintainers:
        - name: Database Team
          email: dba@example.com
      sources:
        - https://github.com/example/mysql-formula
```

### Properties

**Generated by:** `salt-bundle repo index`

**Sort order:**
- Versions sorted newest first within each package

**URL formats:**
- **Relative:** `nginx-2.1.5.tgz` (resolved relative to repository URL)
- **Absolute:** `https://cdn.example.com/packages/nginx-2.1.5.tgz`

**Use `--base-url` for absolute URLs:**
```bash
salt-bundle repo index --base-url https://cdn.example.com/packages/
```

**datetime format:**
- ISO 8601: `YYYY-MM-DDTHH:MM:SSZ`
- Always UTC (Z suffix)

## User Configuration (config.yaml)

### Location

`~/.config/salt-bundle/config.yaml` (Linux/macOS)
`%APPDATA%\salt-bundle\config.yaml` (Windows)

### Format

```yaml
repositories:                   # Global repositories
  - name: string                # Repository name
    url: string                 # Repository URL
allowed_repos: [string, ...]    # Optional: Whitelist of allowed URLs
```

### Example

```yaml
repositories:
  - name: saltstack
    url: https://formulas.saltstack.com/

  - name: company
    url: https://formulas.company.com/

  - name: local
    url: file:///srv/salt-repo/

allowed_repos:
  - https://formulas.saltstack.com/
  - https://formulas.company.com/
  - file:///srv/salt-repo/
```

### Properties

**Created by:** `salt-bundle repo add`

**Managed by:** User

**Priority:**
- Project repositories checked first
- Then global repositories (top to bottom)

**allowed_repos (optional):**
- Security constraint
- If set, blocks repositories not in list
- Applies to both project and global repos

## Package Archive (.tgz)

### Format

Standard gzip-compressed tar archive.

### Contents

```
formula-1.0.0.tgz
├── .saltbundle.yaml      # Required: Metadata
├── init.sls              # Required: At least one .sls
├── install.sls           # Optional: Additional states
├── config.sls
├── map.jinja
├── defaults.yaml
├── files/
│   └── config.conf
├── templates/
│   └── app.conf.j2
└── _modules/
    └── custom.py
```

### Requirements

- Must contain `.saltbundle.yaml`
- Must contain at least one `.sls` file
- All paths relative (no absolute paths)
- No path traversal (`..` not allowed)

### Creation

```bash
salt-bundle formula pack
```

### Extraction

Automatic during installation to `vendor/{package-name}/`.

## Data Types

### String

YAML string, optionally quoted.

```yaml
name: nginx
name: "nginx"
name: 'nginx'
```

### String List

YAML list of strings.

```yaml
keywords:
  - nginx
  - webserver

# Or inline
keywords: [nginx, webserver]
```

### Dictionary

YAML dictionary (key-value pairs).

```yaml
dependencies:
  nginx: "^2.0.0"
  mysql: "~5.7.0"
```

### Object List

YAML list of objects.

```yaml
repositories:
  - name: main
    url: https://example.com/
  - name: backup
    url: https://backup.example.com/
```

### Datetime

ISO 8601 format, UTC timezone.

```yaml
generated: "2025-01-15T10:30:00Z"
created: "2025-01-15T09:00:00.123456Z"
```

**Format:** `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`

## Common Patterns

### Version Constraints

See [Version Constraints](version-constraints.md) for complete reference.

**Examples:**

```yaml
dependencies:
  exact: "1.2.3"                    # Exact version
  caret: "^1.2.3"                   # Compatible (^)
  tilde: "~1.2.3"                   # Patch-level (~)
  wildcard: "1.2.*"                 # Wildcard
  range: ">=1.0,<2.0"               # Range
  repo-specific: "main/package: ^1.0"  # From specific repo
```

### Repository URLs

**HTTP/HTTPS:**
```yaml
url: https://formulas.example.com/
url: http://localhost:8080/
```

**File (absolute path):**
```yaml
url: file:///srv/salt-repo/
url: file:///home/user/formulas/
```

### SHA256 Digest

**Format:**
```yaml
digest: sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

**Components:**
- Prefix: `sha256:`
- Hash: 64 hexadecimal characters (256 bits)

## Validation

### YAML Syntax

All files must be valid YAML:

```bash
# Validate with Python
python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"

# Validate with yq
yq . file.yaml
```

### Schema Validation

Use Salt Bundle models for validation:

```python
import yaml
from salt_bundle.models.package_models import PackageMeta

with open('.saltbundle.yaml') as f:
    data = yaml.safe_load(f)
    meta = PackageMeta(**data)
```

## Best Practices

### File Naming

- Use lowercase
- Use hyphens for readability: `.saltbundle.yaml`, `.salt-dependencies.lock`

### Line Length

- Keep lines under 100 characters
- Use YAML multi-line strings if needed:

```yaml
description: >
  This is a long description
  that spans multiple lines
  but renders as single line
```

### Comments

Use comments for clarity:

```yaml
dependencies:
  # Web tier
  nginx: "^2.0.0"

  # Database tier
  postgresql: "^13.0"
```

### Indentation

- Use 2 spaces (YAML standard)
- Don't mix tabs and spaces

### Quoting

Quote strings with special characters:

```yaml
version: "1.0.0"          # Good
version: 1.0.0            # Also works, but inconsistent

url: "https://example.com/"  # Required (colons)
url: https://example.com/    # Error (unquoted colon)
```

## Next Steps

- [Formula Configuration](formula-configuration.md) - Formula metadata details
- [Project Configuration](project-configuration.md) - Project configuration details
- [Version Constraints](version-constraints.md) - Version constraint formats
- [CLI Reference](cli-reference.md) - Command-line tools
