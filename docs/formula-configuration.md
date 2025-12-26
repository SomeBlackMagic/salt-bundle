# Formula Configuration Reference

Complete reference for `.saltbundle.yaml` configuration in formula packages.

## Overview

The `.saltbundle.yaml` file in a formula directory defines package metadata, dependencies, and compatibility information.

## Basic Structure

```yaml
name: formula-name
version: 1.2.3
description: Brief description of the formula

maintainers:
  - name: Maintainer Name
    email: email@example.com

keywords:
  - tag1
  - tag2

sources:
  - https://github.com/org/repo

salt:
  min_version: "3006"
  max_version: "3009"

dependencies:
  - name: dependency-formula
    version: "^1.0.0"
```

## Fields Reference

### Required Fields

#### `name`

**Type:** String
**Pattern:** `^[a-z0-9_-]+$`
**Required:** Yes

Package identifier. Must be lowercase, alphanumeric with hyphens and underscores.

```yaml
name: nginx             # Good
name: my-formula        # Good
name: app_config        # Good
name: My-Formula        # Bad: uppercase
name: my@formula        # Bad: special characters
```

#### `version`

**Type:** String (Semantic Version)
**Pattern:** `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`
**Required:** Yes

Semantic version following [semver.org](https://semver.org/) specification.

```yaml
version: 1.0.0          # Release
version: 1.2.3          # Release
version: 2.0.0-alpha    # Pre-release
version: 1.5.0-beta.1   # Pre-release with number
version: 1.0.0+build123 # With build metadata
```

**Version increment guidelines:**
- **MAJOR**: Breaking changes (incompatible with previous version)
- **MINOR**: New features (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Optional Fields

#### `description`

**Type:** String
**Default:** None

Short description of the formula's purpose.

```yaml
description: Nginx web server configuration and management
```

#### `maintainers`

**Type:** List of objects
**Default:** Empty list

List of people maintaining the formula.

```yaml
maintainers:
  - name: John Doe
    email: john@example.com
  - name: Jane Smith
    email: jane@example.com
  - name: DevOps Team
    # email is optional
```

**Fields:**
- `name` (required): Maintainer's name
- `email` (optional): Contact email

#### `keywords`

**Type:** List of strings
**Default:** Empty list

Tags for categorizing and searching formulas.

```yaml
keywords:
  - webserver
  - nginx
  - reverse-proxy
  - ssl
  - http
```

#### `sources`

**Type:** List of URLs
**Default:** Empty list

Links to source repositories, documentation, or related resources.

```yaml
sources:
  - https://github.com/organization/formula-repo
  - https://nginx.org/
  - https://docs.example.com/formulas/nginx
```

#### `salt`

**Type:** Object
**Default:** None

Salt version compatibility constraints.

```yaml
salt:
  min_version: "3006"
  max_version: "3009"
```

**Fields:**
- `min_version` (optional): Minimum compatible Salt version
- `max_version` (optional): Maximum compatible Salt version

**Version format:**
- Use Salt's version numbers: `3006`, `3007`, `3008`, `3009`
- Or full versions: `3006.0`, `3007.1`

**Examples:**

```yaml
# Any Salt 3006 or newer
salt:
  min_version: "3006"

# Only Salt 3006-3008
salt:
  min_version: "3006"
  max_version: "3008"

# Only Salt 3007
salt:
  min_version: "3007"
  max_version: "3007"
```

#### `dependencies`

**Type:** List of objects
**Default:** Empty list

Formula dependencies with version constraints.

```yaml
dependencies:
  - name: common
    version: "^1.0.0"
  - name: firewall
    version: "~2.3"
  - name: users
    version: ">=1.5,<2.0"
```

**Fields:**
- `name` (required): Dependency formula name
- `version` (required): Version constraint

See [Version Constraints](version-constraints.md) for constraint formats.

**Examples:**

```yaml
# No dependencies
dependencies: []

# Single dependency
dependencies:
  - name: common
    version: "^1.0"

# Multiple dependencies
dependencies:
  - name: common
    version: "^1.0.0"
  - name: firewall
    version: "~2.3.0"
  - name: users
    version: ">=1.0,<2.0"
```

#### `entry`

**Type:** Object
**Default:** None
**Status:** Reserved for future use

Entry points configuration for the formula.

```yaml
entry:
  states_root: "."
  pillar_root: "pillar"
  modules:
    - "_modules"
    - "_states"
    - "_grains"
```

**Fields:**
- `states_root`: Root directory for state files (default: ".")
- `pillar_root`: Root directory for pillar files
- `modules`: List of custom module directories

## Complete Examples

### Simple Formula

```yaml
name: hello-world
version: 1.0.0
description: Simple hello world formula
```

### Production Formula

```yaml
name: nginx
version: 2.1.0
description: Nginx web server with SSL support and reverse proxy configuration

maintainers:
  - name: DevOps Team
    email: devops@example.com
  - name: Infrastructure Team
    email: infra@example.com

keywords:
  - nginx
  - webserver
  - reverse-proxy
  - ssl
  - http
  - https
  - load-balancer

sources:
  - https://github.com/example/salt-nginx
  - https://nginx.org/
  - https://example.com/docs/nginx-formula

salt:
  min_version: "3006"
  max_version: "3009"

dependencies:
  - name: common
    version: "^1.0.0"
  - name: firewall
    version: "~2.3.0"
  - name: ssl-certs
    version: ">=1.2,<2.0"
```

### Formula with Many Dependencies

```yaml
name: application-stack
version: 3.0.0
description: Complete application stack with web server, database, and cache

maintainers:
  - name: Platform Team
    email: platform@example.com

keywords:
  - application
  - stack
  - nginx
  - postgresql
  - redis

sources:
  - https://github.com/example/app-stack-formula

salt:
  min_version: "3007"

dependencies:
  - name: nginx
    version: "^2.0.0"
  - name: postgresql
    version: "^13.0"
  - name: redis
    version: "^6.2"
  - name: python
    version: "^3.9"
  - name: supervisor
    version: "~4.2"
  - name: logrotate
    version: ">=1.0,<2.0"
```

### Pre-release Formula

```yaml
name: experimental-feature
version: 1.0.0-beta.1
description: Experimental feature - use at your own risk

maintainers:
  - name: Research Team
    email: research@example.com

keywords:
  - experimental
  - beta
  - testing

sources:
  - https://github.com/example/experimental

salt:
  min_version: "3008"

dependencies:
  - name: common
    version: "^2.0.0"
```

## Validation

### Validate Locally

Check your configuration is valid:

```bash
# Try to pack (validates metadata)
salt-bundle formula pack

# Or use Python
python3 << 'EOF'
import yaml
from salt_bundle.models.package_models import PackageMeta

with open('.saltbundle.yaml') as f:
    data = yaml.safe_load(f)
    meta = PackageMeta(**data)
    print(f"Valid: {meta.name} {meta.version}")
EOF
```

### Common Validation Errors

#### Invalid Package Name

```yaml
# Error: uppercase not allowed
name: My-Formula

# Fix
name: my-formula
```

#### Invalid Semantic Version

```yaml
# Error: missing patch version
version: 1.2

# Fix
version: 1.2.0
```

#### Missing Required Field

```yaml
# Error: name is required
version: 1.0.0

# Fix
name: my-formula
version: 1.0.0
```

#### Invalid YAML Syntax

```yaml
# Error: invalid YAML
dependencies
  - name: common
    version: ^1.0

# Fix
dependencies:
  - name: common
    version: "^1.0"
```

## Best Practices

### Naming

- Use lowercase only
- Use hyphens for multi-word names: `my-formula`
- Be descriptive: `nginx-reverse-proxy` vs `nginx`
- Avoid generic names: `app`, `service`, `formula`

### Versioning

- Start at `1.0.0` for production-ready formulas
- Use `0.x.x` for pre-production development
- Follow semver strictly
- Document breaking changes in CHANGELOG.md

### Description

- Keep it concise (one sentence)
- Focus on what the formula does
- Mention key features

```yaml
# Good
description: Nginx web server with SSL and reverse proxy support

# Too vague
description: Web server formula

# Too detailed (use README instead)
description: |
  This formula installs and configures Nginx web server.
  It supports SSL certificates, reverse proxy configuration,
  load balancing, caching, and more.
```

### Keywords

- 3-7 keywords is optimal
- Use technology names
- Include use cases
- Avoid redundancy with name

```yaml
# Good
name: nginx
keywords:
  - webserver
  - reverse-proxy
  - ssl
  - http

# Bad (redundant)
name: nginx
keywords:
  - nginx
  - nginx-server
  - nginx-formula
```

### Dependencies

- Only declare direct dependencies
- Use appropriate constraints (see [Version Constraints](version-constraints.md))
- Keep dependencies minimal
- Document dependency usage in README

```yaml
# Good: specific versions
dependencies:
  - name: common
    version: "^1.5.0"
  - name: firewall
    version: "~2.3.1"

# Avoid: too permissive
dependencies:
  - name: common
    version: "*"
```

### Salt Compatibility

- Test with specified Salt versions
- Be conservative with max_version
- Update as you test new Salt versions

```yaml
# Good: tested range
salt:
  min_version: "3006"
  max_version: "3009"

# Avoid: untested range
salt:
  min_version: "3000"
  max_version: "3999"
```

## Migration from Other Formats

### From Helm Chart.yaml

```yaml
# Helm Chart.yaml
name: nginx
version: 2.1.0
appVersion: 1.21.0
description: Nginx web server
maintainers:
  - name: Developer
    email: dev@example.com
dependencies:
  - name: common
    version: ^1.0.0
    repository: https://charts.example.com/

# Salt Bundle .saltbundle.yaml
name: nginx
version: 2.1.0
description: Nginx web server
maintainers:
  - name: Developer
    email: dev@example.com
dependencies:
  - name: common
    version: "^1.0.0"
# Note: repository is configured separately in project config
```

### From Formula Metadata

If you have existing formula metadata in different format, convert to `.saltbundle.yaml`:

```yaml
# Old metadata format
formula:
  name: nginx
  version: 2.1.0

# New .saltbundle.yaml
name: nginx
version: 2.1.0
```

## Next Steps

- [Publishing Guide](publishing-guide.md) - Pack and publish your formula
- [Version Constraints](version-constraints.md) - Understanding dependencies
- [Project Configuration](project-configuration.md) - Using formulas in projects
