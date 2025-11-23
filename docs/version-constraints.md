# Version Constraints Guide

This guide explains how to specify version constraints for Salt formula dependencies using semantic versioning.

## Table of Contents

- [Semantic Versioning](#semantic-versioning)
- [Constraint Formats](#constraint-formats)
- [Examples](#examples)
- [Resolution Behavior](#resolution-behavior)
- [Best Practices](#best-practices)

## Semantic Versioning

Salt Bundle uses [Semantic Versioning (semver)](https://semver.org/) for formula versions.

### Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible new features
- **PATCH**: Backwards-compatible bug fixes
- **PRERELEASE**: Optional (e.g., `-alpha`, `-beta.1`, `-rc.2`)
- **BUILD**: Optional metadata (e.g., `+20230615`)

### Examples

```
1.0.0          # Release version
1.2.3          # Standard version
2.0.0-alpha    # Pre-release
1.5.0-beta.1   # Pre-release with number
1.0.0+20230615 # With build metadata
```

### Version Comparison

```
0.1.0 < 0.2.0 < 0.2.1 < 1.0.0 < 1.0.1 < 1.1.0 < 2.0.0

# Pre-releases come before releases
1.0.0-alpha < 1.0.0-beta < 1.0.0-rc.1 < 1.0.0

# Build metadata is ignored in comparison
1.0.0+build1 == 1.0.0+build2
```

## Constraint Formats

### Exact Version

Matches exactly one version.

```yaml
dependencies:
  nginx: "2.1.5"
```

**Matches:** `2.1.5`
**Doesn't match:** `2.1.4`, `2.1.6`, `2.2.0`

**Use when:** You need a specific version for compatibility.

### Caret (^) - Compatible Releases

Allows changes that don't modify the left-most non-zero digit.

```yaml
dependencies:
  nginx: "^2.1.5"
```

**Behavior:**
- `^1.2.3` → `>=1.2.3, <2.0.0` (1.x.x family)
- `^0.2.3` → `>=0.2.3, <0.3.0` (0.2.x family, major 0 is special)
- `^0.0.3` → `>=0.0.3, <0.0.4` (0.0.x, exact patch)

**Examples:**

| Constraint | Matches | Doesn't Match |
|------------|---------|---------------|
| `^2.1.5` | `2.1.5`, `2.2.0`, `2.9.9` | `2.1.4`, `3.0.0` |
| `^1.0.0` | `1.0.0`, `1.5.0`, `1.9.9` | `0.9.9`, `2.0.0` |
| `^0.2.3` | `0.2.3`, `0.2.9` | `0.2.2`, `0.3.0` |

**Use when:** You want new features and bug fixes, but not breaking changes.

### Tilde (~) - Patch-Level Changes

Allows patch-level changes only.

```yaml
dependencies:
  mysql: "~5.7.8"
```

**Behavior:**
- `~1.2.3` → `>=1.2.3, <1.3.0` (1.2.x family)
- `~1.2` → `>=1.2.0, <1.3.0` (same as ~1.2.0)
- `~0` → `>=0.0.0, <1.0.0` (0.x.x family)

**Examples:**

| Constraint | Matches | Doesn't Match |
|------------|---------|---------------|
| `~5.7.8` | `5.7.8`, `5.7.9`, `5.7.15` | `5.7.7`, `5.8.0` |
| `~1.2.3` | `1.2.3`, `1.2.9` | `1.2.2`, `1.3.0` |
| `~0.2` | `0.2.0`, `0.2.9` | `0.1.9`, `0.3.0` |

**Use when:** You only want bug fixes, no new features.

### Wildcard (*, x) - Flexible Versions

Wildcards match any value in that position.

```yaml
dependencies:
  redis: "6.2.*"
  # Or equivalently:
  redis: "6.2.x"
```

**Examples:**

| Constraint | Matches | Doesn't Match |
|------------|---------|---------------|
| `1.2.*` | `1.2.0`, `1.2.5`, `1.2.99` | `1.1.9`, `1.3.0` |
| `1.*` | `1.0.0`, `1.5.0`, `1.99.99` | `0.9.9`, `2.0.0` |
| `*` | Any version | None |

**Use when:** You want maximum flexibility in a version range.

### Comparison Operators

Explicit version ranges using comparison operators.

```yaml
dependencies:
  # Greater than or equal
  nginx: ">=2.0.0"

  # Less than
  mysql: "<6.0.0"

  # Greater than
  redis: ">5.0.0"

  # Less than or equal
  postgresql: "<=12.5"

  # Equal (same as exact)
  memcached: "=1.6.9"
```

**Operators:**
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `>` - Greater than
- `<` - Less than
- `=` - Equal to

### Range Constraints

Combine multiple constraints with commas.

```yaml
dependencies:
  # Between 1.0 and 2.0 (excluding 2.0)
  postgresql: ">=12.0,<14.0"

  # At least 1.5, but not 2.0 or higher
  nginx: ">=1.5,<2.0"

  # Greater than 1.0, less than or equal to 1.9
  redis: ">1.0,<=1.9"
```

**Examples:**

| Constraint | Matches | Doesn't Match |
|------------|---------|---------------|
| `>=1.0,<2.0` | `1.0.0`, `1.5.0`, `1.9.9` | `0.9.9`, `2.0.0` |
| `>=1.2,<1.5` | `1.2.0`, `1.3.0`, `1.4.9` | `1.1.9`, `1.5.0` |

**Use when:** You need precise control over version range.

## Examples

### Common Patterns

```yaml
dependencies:
  # Latest 2.x (recommended)
  nginx: "^2.0.0"

  # Latest 1.2.x patches only
  mysql: "~1.2.0"

  # Any 6.x version
  redis: "6.*"

  # At least 3.0, less than 4.0
  postgresql: ">=3.0,<4.0"

  # Exact version
  memcached: "1.6.9"

  # Latest 0.x (pre-1.0 package)
  experimental: "^0.5.0"
```

### Pre-release Versions

```yaml
dependencies:
  # Only stable releases
  nginx: "^2.0.0"

  # Include pre-releases
  testing: "^1.0.0-alpha"
```

**Note:** Pre-release versions are only matched explicitly:

```yaml
# Does NOT match 1.0.0-beta
nginx: "^1.0.0"

# DOES match 1.0.0-beta, 1.0.0-rc.1, 1.0.0
nginx: "^1.0.0-alpha"
```

### Repository-Specific Versions

```yaml
dependencies:
  # From any repository
  nginx: "^2.0.0"

  # From specific repository
  company/internal: "^1.0.0"

  # Different constraints per repository
  main/redis: "^6.0.0"
  testing/redis: "^7.0.0-beta"
```

## Resolution Behavior

### Latest Compatible Version

Salt Bundle always resolves to the **latest version** matching constraints.

**Example:**

Given repository with versions:
```
nginx: 2.0.0, 2.1.0, 2.1.5, 2.2.0, 3.0.0
```

Constraint `nginx: "^2.0.0"` resolves to `2.2.0` (latest 2.x).

### Multiple Repositories

When searching multiple repositories, first match wins:

```yaml
repositories:
  - name: main
    url: https://main-repo.com/    # Checked first
  - name: backup
    url: https://backup-repo.com/  # Checked second

dependencies:
  nginx: "^2.0.0"
```

**Resolution:**
1. Check `main` for nginx 2.x → Found `2.2.0` → Use it
2. Skip `backup` (already resolved)

**With repository prefix:**

```yaml
dependencies:
  # Only check 'backup' repository
  backup/nginx: "^2.0.0"
```

### Lock File Priority

When `salt-bundle.lock` exists:

```bash
# Uses lock file (exact versions)
salt-bundle install

# Ignores lock file (re-resolves)
salt-bundle install --no-lock

# Updates lock file with new versions
salt-bundle install --update-lock
```

### Conflict Resolution

Salt Bundle currently doesn't handle transitive dependencies. Each dependency is resolved independently.

**Example:**

```yaml
# Your project
dependencies:
  app: "^1.0.0"
  common: "^2.0.0"

# app depends on common ^1.0.0
# This creates a potential conflict
```

**Solution:** Ensure compatible version ranges or use exact versions.

## Best Practices

### For Formula Publishers

**Be conservative with breaking changes:**

```yaml
# Good: Increment major version for breaking changes
version: 2.0.0  # Breaking change from 1.x

# Good: Increment minor for new features
version: 1.5.0  # New optional parameters

# Good: Increment patch for bug fixes
version: 1.4.1  # Bug fix
```

**Declare dependencies precisely:**

```yaml
dependencies:
  # Too loose (may break)
  common: "*"

  # Better (allows compatible updates)
  common: "^1.0"

  # Best (specific compatibility)
  common: "^1.5.0"
```

### For Formula Consumers

**Use caret for libraries:**

```yaml
dependencies:
  # Good: Allows bug fixes and features
  nginx: "^2.0.0"

  # Good: Allows patches only
  mysql: "~5.7.8"
```

**Lock critical versions:**

```yaml
dependencies:
  # Production-critical: exact version
  payment-gateway: "3.2.1"

  # Less critical: flexible
  monitoring: "^2.0.0"
```

**Test before updating:**

```bash
# Test with latest versions
salt-bundle install --update-lock --dry-run

# If safe, update
salt-bundle install --update-lock

# Test changes
./salt.sh state.apply test=True

# Commit lock file
git commit salt-bundle.lock -m "Update dependencies"
```

### Version Constraint Strategy

| Scenario | Constraint | Example |
|----------|------------|---------|
| Active development | Caret `^` | `^1.5.0` |
| Stable production | Tilde `~` | `~2.3.1` |
| Critical systems | Exact | `1.2.3` |
| Testing/bleeding edge | Range | `>=2.0,<3.0` |
| Maximum compatibility | Wildcard | `2.*` |

## Common Mistakes

### Mistake 1: Too Permissive

```yaml
# Bad: Will accept breaking changes
dependencies:
  nginx: "*"
  mysql: ">=1.0.0"
```

**Fix:**
```yaml
# Good: Controlled updates
dependencies:
  nginx: "^2.0.0"
  mysql: "^5.7.0"
```

### Mistake 2: Too Restrictive

```yaml
# Bad: Misses bug fixes
dependencies:
  nginx: "2.1.5"
  mysql: "5.7.8"
```

**Fix:**
```yaml
# Good: Allow patches
dependencies:
  nginx: "~2.1.5"
  mysql: "~5.7.8"
```

### Mistake 3: Wrong Format

```yaml
# Bad: Invalid semver
dependencies:
  nginx: "v2.1.5"   # No 'v' prefix
  mysql: "5.7"      # Missing patch version
```

**Fix:**
```yaml
# Good: Valid semver
dependencies:
  nginx: "2.1.5"    # Or "^2.1.5"
  mysql: "5.7.0"    # Or "~5.7"
```

### Mistake 4: Ignoring Pre-releases

```yaml
# This won't match 1.0.0-beta
dependencies:
  new-formula: "^1.0.0"
```

**Fix:**
```yaml
# Explicitly allow pre-releases if needed
dependencies:
  new-formula: "^1.0.0-alpha"
```

## Testing Version Constraints

### Manual Testing

```bash
# Create test project
mkdir test-versions
cd test-versions
salt-bundle init --project

# Test constraint
cat > .saltbundle.yaml << EOF
project: test
dependencies:
  nginx: "^2.0.0"
EOF

# See what resolves
salt-bundle install

# Check locked version
cat salt-bundle.lock
```

### Check Available Versions

```bash
# Download repository index
curl https://repo.example.com/index.yaml

# View available versions
yq '.packages.nginx[].version' index.yaml
```

## Next Steps

- [Installation Guide](installation-guide.md) - Using constraints in projects
- [Publishing Guide](publishing-guide.md) - Creating versioned formulas
- [Project Configuration](project-configuration.md) - Complete configuration reference
