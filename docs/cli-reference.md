# CLI Reference

Complete command-line interface reference for Salt Bundle.

## Global Options

Available for all commands:

```bash
salt-bundle [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]
```

| Option                          | Description                                    |
|---------------------------------|------------------------------------------------|
| `--debug`                       | Enable debug output                            |
| `--quiet`                       | Suppress output                                |
| `--project-dir PATH`, `-C PATH` | Project directory (default: current directory) |
| `--help`                        | Show help message                              |
| `--version`                     | Show version                                   |

## Command Structure

Salt Bundle now uses a hierarchical command structure with three main groups:

- **`formula`** - Commands for managing Salt formulas
- **`project`** - Commands for managing Salt projects and dependencies
- **repo`** - Commands for managing formula repositories

## Formula Commands

Commands for creating, packaging, and managing Salt formulas.

### formula init

Initialize a new Salt formula configuration.

```bash
salt-bundle package init [OPTIONS]
```

**Options:**

| Option    | Description                      |
|-----------|----------------------------------|
| `--force` | Overwrite existing configuration |

**Examples:**

```bash
# Initialize formula interactively
cd my-formula
salt-bundle package init

# Force overwrite existing config
salt-bundle package init --force

# Initialize in specific directory
salt-bundle package init -C /path/to/package
```

**Creates:**
- `FORMULA` with formula metadata

**Interactive prompts:**
- Formula name
- Version
- Description
- Salt min version (optional)
- Salt max version (optional)

---

### formula pack

Package a Salt formula into a distributable tar.gz archive.

```bash
salt-bundle package pack [OPTIONS]
```

**Options:**

| Option                         | Description                                               |
|--------------------------------|-----------------------------------------------------------|
| `--output-dir PATH`, `-o PATH` | Output directory for archive (default: current directory) |

**Examples:**

```bash
# Pack formula in current directory
cd my-formula
salt-bundle package pack

# Pack to specific directory
salt-bundle package pack --output-dir /path/to/output

# Pack from different directory
salt-bundle package pack -C /path/to/package
```

**Output:**
- `{name}-{version}.tar.gz` archive

**Requirements:**
- `FORMULA` must exist
- Valid semver version
- Valid package name

---

### formula verify

Verify integrity of installed formula dependencies.

```bash
salt-bundle package verify
```

**Examples:**

```bash
# Verify all dependencies
salt-bundle package verify

# Verify in specific project directory
salt-bundle package verify -C /path/to/project
```

**Checks:**
- All packages from lock file are installed
- `FORMULA` exists in each package
- Package versions match lock file

**Exit codes:**
- `0` - All dependencies verified
- `1` - Errors found

---

### formula sync

Sync vendor formula modules to Salt's extension modules cache.

```bash
salt-bundle package sync [OPTIONS]
```

**Options:**

| Option             | Description                                           |
|--------------------|-------------------------------------------------------|
| `--cache-dir PATH` | Salt cache directory (auto-detected if not specified) |

**Examples:**

```bash
# Auto-detect cache directory and sync
salt-bundle package sync

# Specify custom cache directory
salt-bundle package sync --cache-dir /var/cache/salt/minion/extmods

# Sync from different project directory
salt-bundle package sync -C /path/to/project
```

**Module types synchronized:**
- modules, states, grains, pillar, returners, runners
- output, utils, renderers, engines, proxy, beacons

**Behavior:**
- Copies custom modules from vendor formulas
- Runs `salt-call --local saltutil.sync_all` automatically

---

## Project Commands

Commands for managing Salt projects with formula dependencies.

### project init

Initialize a new Salt project with dependency management.

```bash
salt-bundle project init [OPTIONS]
```

**Options:**

| Option    | Description                      |
|-----------|----------------------------------|
| `--force` | Overwrite existing configuration |

**Examples:**

```bash
# Initialize project interactively
mkdir my-project
cd my-project
salt-bundle project init

# Force overwrite existing configuration
salt-bundle project init --force

# Initialize in specific directory
salt-bundle project init -C /path/to/project
```

**Creates:**
- `Saltfile` with project configuration

**Next steps displayed:**
1. Add dependency objects to `Saltfile`
2. Add a `source` that contains `index.yaml`, or register a global source with `salt-bundle repo add`
3. Resolve and install: `salt-bundle project update`

---

### project install

Install project dependencies from lock file.

```bash
salt-bundle project install
```

**Examples:**

```bash
# Install from lock file
salt-bundle project install

# Install in different directory
salt-bundle project install -C /path/to/project
```

**Behavior:**
- Reads `Saltfile.lock` for exact versions
- Downloads packages from configured repositories
- Installs to vendor directory
- Syncs Salt extensions automatically

**Requirements:**
- `Saltfile` must exist
- `Saltfile.lock` must exist
- At least one repository configured

**Exit codes:**
- `0` - Installation successful
- `1` - Error occurred

**Use cases:**
- Production deployments
- CI/CD pipelines
- Reproducible installations

---

### project update

Resolve dependencies and update lock file.

```bash
salt-bundle project update
```

**Examples:**

```bash
# Resolve and install all dependencies
salt-bundle project update

# Update in specific project directory
salt-bundle project update -C /path/to/project
```

**Behavior:**
1. Reads direct dependencies from `Saltfile`
2. Queries configured repositories for available versions
3. **Recursively resolves** transitive dependencies (dependencies of dependencies)
4. Resolves version constraints to the best matching versions
5. Creates or updates `Saltfile.lock` with the full tree of resolved packages
6. Downloads and installs all resolved packages to the vendor directory
7. Syncs Salt extensions

**Dependency resolution:**
- Uses a dependency's `source` repository, or global user repositories when `source` is omitted
- Each source must provide `index.yaml`
- Resolves version constraints (e.g., `>=1.0.0`, `~1.2.0`, `^1.0.0`)
- Automatically discovers and pulls in transitive dependencies defined in formula `FORMULA` files
- Fails if any dependency in the tree cannot be resolved or if there are unresolvable version conflicts

**Use cases:**
- Adding new dependencies
- Updating to newer versions
- Initial project setup

**Exit codes:**
- `0` - Dependencies resolved and installed
- `1` - Resolution or installation failed

---

### project vendor

Install dependencies from lock file (reproducible deploy).

```bash
salt-bundle project vendor
```

**Examples:**

```bash
# Install from lock file
salt-bundle project vendor

# Install in specific project directory
salt-bundle project vendor -C /path/to/project
```

**Behavior:**
- Alias for `salt-bundle project install`
- Only uses `Saltfile.lock`
- No dependency resolution

**Use cases:**
- Production deployments
- CI/CD pipelines
- Team collaboration
- Ensuring consistent environments

---

## Repository Commands

Commands for managing formula repositories.

### repo add

Add a formula repository to project or global configuration.

```bash
salt-bundle repo add --name NAME --url URL
```

**Options:**

| Option        | Description                              |
|---------------|------------------------------------------|
| `--name NAME` | Repository name (unique identifier)      |
| `--url URL`   | Repository URL (must contain index.yaml) |

**Examples:**

```bash
# Add remote repository to project
salt-bundle repo add --name official --url https://formulas.example.com/

# Add local repository
salt-bundle repo add --name local --url file:///opt/formulas/

# Add to global configuration (no project found)
cd /tmp
salt-bundle repo add --name global --url https://repo.example.com/
```

**Repository types:**
- HTTP/HTTPS: Remote repositories
- File: Local directories (`file:///path/to/repo/`)
- GitHub Pages: Static hosting

**Behavior:**
- If `Saltfile` exists: adds to project
- Otherwise: adds to global user config (`~/.salt-bundle/config.yaml`)

---

### repo index

Generate or update repository index from formula packages.

```bash
salt-bundle repo index [DIRECTORY] [OPTIONS]
```

**Arguments:**

| Argument    | Description                                                       |
|-------------|-------------------------------------------------------------------|
| `DIRECTORY` | Directory containing `.tar.gz` files (default: current directory) |

**Options:**

| Option                         | Description                                                          |
|--------------------------------|----------------------------------------------------------------------|
| `--output-dir PATH`, `-o PATH` | Output directory for `index.yaml` (default: same as input directory) |
| `--base-url URL`, `-u URL`     | Base URL for package links in index                                  |

**Examples:**

```bash
# Generate index in current directory
cd /srv/salt-repo
salt-bundle repo index

# Generate for specific directory
salt-bundle repo index /path/to/repo

# With base URL (absolute URLs)
salt-bundle repo index --base-url https://formulas.example.com/

# Output to different directory
salt-bundle repo index /srv/packages --output-dir /srv/repo
```

**Output:**
- `index.yaml` with all package versions

**Behavior:**
- Scans directory for `.tar.gz` files
- Reads metadata from each archive
- Calculates SHA256 digests
- Merges with existing `index.yaml` (if present)
- Sorts versions (newest first)

---

### repo release

Release formulas to repository (automated packaging and publishing).

```bash
salt-bundle repo release --formulas-dir PATH --provider PROVIDER [OPTIONS]
```

**Required Options:**

| Option                               | Description                                      |
|--------------------------------------|--------------------------------------------------|
| `--formulas-dir PATH`, `-f PATH`     | Directory containing formulas (required)         |
| `--provider PROVIDER`, `-p PROVIDER` | Release provider: `local` or `github` (required) |

**Provider: local**

| Option                   | Description                                                |
|--------------------------|------------------------------------------------------------|
| `--pkg-storage-dir PATH` | Directory for packages and index.yaml (required for local) |

**Provider: github**

Requires environment variables:
- `GITHUB_TOKEN` - Personal access token with `repo` permissions
- `GITHUB_REPOSITORY` - Repository in format `owner/repo`

| Option                  | Description                                     |
|-------------------------|-------------------------------------------------|
| `--index-branch BRANCH` | Git branch for index.yaml (default: `gh-pages`) |

**Common Options:**

| Option             | Description                                               |
|--------------------|-----------------------------------------------------------|
| `--single`         | Treat formulas-dir as single formula (not subdirectories) |
| `--skip-packaging` | Skip packaging step (use existing .tgz files)             |
| `--dry-run`        | Show what would be done without doing it                  |

**Examples:**

```bash
# Local provider - multiple formulas
cd formulas/
salt-bundle repo release \
  --formulas-dir . \
  --provider local \
  --pkg-storage-dir /srv/salt-repo

# Local provider - single formula
cd my-formula
salt-bundle repo release \
  --formulas-dir . \
  --single \
  --provider local \
  --pkg-storage-dir /srv/salt-repo

# GitHub provider - multiple formulas
export GITHUB_TOKEN=ghp_xxxx
export GITHUB_REPOSITORY=owner/repo
cd formulas/
salt-bundle repo release \
  --formulas-dir . \
  --provider github

# GitHub provider - single formula
cd my-formula
export GITHUB_TOKEN=ghp_xxxx
export GITHUB_REPOSITORY=owner/repo
salt-bundle repo release \
  --formulas-dir . \
  --single \
  --provider github

# Custom index branch
salt-bundle repo release \
  --formulas-dir . \
  --provider github \
  --index-branch main

# Dry run mode
salt-bundle repo release \
  --formulas-dir . \
  --provider local \
  --pkg-storage-dir /tmp/test \
  --dry-run

# Skip packaging (use existing .tgz)
salt-bundle repo release \
  --formulas-dir . \
  --provider local \
  --pkg-storage-dir /srv/repo \
  --skip-packaging
```

**Workflow:**

1. **Discovery** - Scans for formulas
2. **Version Check** - Checks which versions are new
3. **Packaging** - Packs new versions (unless `--skip-packaging`)
4. **Publishing** - Uploads to provider
5. **Index Update** - Updates `index.yaml`

---

## Configuration Files

### Project: Saltfile

Location: Project root

```yaml
vendor_dir: vendor

dependencies:
  - name: nginx
    version: "^2.0.0"
    source: https://salt-formulas.example.com/
  - name: mysql
    version: "~5.7.0"
```

See [Project Configuration](project-configuration.md).

---

### Formula: FORMULA

Location: Formula root

```yaml
name: my-formula
version: 1.0.0
description: My Salt formula
formula_path: formula  # Optional: package files from this relative subdirectory

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

See [Formula Configuration](formula-configuration.md).

---

### Lock File: Saltfile.lock

Location: Project root (generated)

```yaml
dependencies:
  package-name:
    version: 1.2.3
    repository: https://formulas.example.com/
    url: https://example.com/package-1.2.3.tgz
    digest: sha256:abc123...
    type: formula
```

---

### User Config: ~/.salt-bundle/config.yaml

Global user configuration.

```yaml
repositories:
  - name: main
    url: https://formulas.example.com/
  - name: local
    url: file:///srv/salt-repo/
```

---

## Common Workflows

### Publishing Workflow

```bash
# 1. Create/edit formula
cd my-formula
vim FORMULA  # Update version

# 2. Pack
salt-bundle package pack

# 3. Copy to repository
cp my-formula-1.0.0.tar.gz /srv/salt-repo/

# 4. Update index
cd /srv/salt-repo
salt-bundle repo index
```

Or use `release` command:

```bash
cd my-formula
salt-bundle repo release \
  --formulas-dir . \
  --single \
  --provider local \
  --pkg-storage-dir /srv/salt-repo
```

---

### Installation Workflow

```bash
# 1. Create project
mkdir my-project
cd my-project
salt-bundle project init

# 2. Add repository
salt-bundle repo add --name main --url https://formulas.example.com/

# 3. Edit dependencies
vim Saltfile

# 4. Update (resolve and install)
salt-bundle project update

# 5. Verify
salt-bundle package verify
```

---

### Update Workflow

```bash
# 1. Update to latest versions
salt-bundle project update

# 2. Test
./test.sh

# 3. Commit if successful
git add Saltfile.lock
git commit -m "Update dependencies"
```

---

## Exit Codes

| Code | Meaning        |
|------|----------------|
| `0`  | Success        |
| `1`  | Error occurred |

---

## Environment Variables

### GITHUB_TOKEN

GitHub personal access token for `github` provider.

**Required permissions:**
- `repo` (full repository access)

**Create token:**
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select `repo` scope
4. Copy token

**Usage:**

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
salt-bundle repo release --provider github ...
```

---

### GITHUB_REPOSITORY

GitHub repository in format `owner/repo`.

**Usage:**

```bash
export GITHUB_REPOSITORY=myorg/salt-formulas
salt-bundle repo release --provider github ...
```

---

## Debugging

### Enable Debug Mode

```bash
salt-bundle --debug project install
```

**Output includes:**
- HTTP requests/responses
- File operations
- Dependency resolution details
- Stack traces on errors

---

### Quiet Mode

```bash
salt-bundle --quiet project install
```

Suppresses all output except errors.

---

### Check Version

```bash
salt-bundle --version
```

---

## Quick Reference

### Formula Developer

```bash
salt-bundle package init          # Initialize package
salt-bundle package pack           # Package package
salt-bundle repo release ...       # Publish to repository
```

### Project Developer

```bash
salt-bundle project init           # Initialize project
salt-bundle repo add ...           # Add repository
salt-bundle project update         # Resolve and install
salt-bundle project install        # Install from lock
salt-bundle package verify         # Verify installation
salt-bundle package sync           # Sync to Salt cache
```

### Repository Manager

```bash
salt-bundle repo index             # Generate index
salt-bundle repo release ...       # Automated release
```

---

## Next Steps

- [Installation Guide](installation-guide.md) - Using CLI for installation
- [Publishing Guide](publishing-guide.md) - Using CLI for publishing
- [Project Configuration](project-configuration.md) - Configuration reference
- [Formula Configuration](formula-configuration.md) - Formula metadata
