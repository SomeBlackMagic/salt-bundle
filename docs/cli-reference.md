# CLI Reference

Complete command-line interface reference for Salt Bundle.

## Global Options

Available for all commands:

```bash
salt-bundle [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

| Option                          | Description                                    |
|---------------------------------|------------------------------------------------|
| `--debug`                       | Enable debug output                            |
| `--quiet`                       | Suppress output                                |
| `--project-dir PATH`, `-C PATH` | Project directory (default: current directory) |
| `--help`                        | Show help message                              |

## Commands

### init

Initialize Salt Bundle configuration.

```bash
salt-bundle init --project
salt-bundle init --formula
```

**Options:**

| Option      | Description                      |
|-------------|----------------------------------|
| `--project` | Initialize project configuration |
| `--formula` | Initialize formula configuration |
| `--force`   | Overwrite existing configuration |

**Examples:**

```bash
# Initialize project
mkdir my-project
cd my-project
salt-bundle init --project

# Initialize formula
mkdir my-formula
cd my-formula
salt-bundle init --formula

# Force overwrite existing config
salt-bundle init --formula --force
```

**Creates:**
- `.saltbundle.yaml` in current directory

**Interactive prompts:**
- Project/Formula name
- Version
- Description (formula only)
- Salt compatibility (formula only)

### pack

Pack formula into tar.gz archive.

```bash
salt-bundle pack [OPTIONS]
```

**Options:**

| Option                         | Description                                               |
|--------------------------------|-----------------------------------------------------------|
| `--output-dir PATH`, `-o PATH` | Output directory for archive (default: current directory) |

**Examples:**

```bash
# Pack formula in current directory
cd my-formula
salt-bundle pack

# Pack to specific directory
salt-bundle pack --output-dir /path/to/output

# Pack from different directory
salt-bundle --project-dir /path/to/formula pack
```

**Output:**
- `{name}-{version}.tgz` archive

**Requirements:**
- `.saltbundle.yaml` must exist
- At least one `.sls` file must exist
- Valid semver version
- Valid package name

### index

Generate or update repository index.

```bash
salt-bundle index [DIRECTORY] [OPTIONS]
```

**Arguments:**

| Argument    | Description                                                    |
|-------------|----------------------------------------------------------------|
| `DIRECTORY` | Directory containing `.tgz` files (default: current directory) |

**Options:**

| Option                         | Description                                                          |
|--------------------------------|----------------------------------------------------------------------|
| `--output-dir PATH`, `-o PATH` | Output directory for `index.yaml` (default: same as input directory) |
| `--base-url URL`, `-u URL`     | Base URL for package links in index                                  |

**Examples:**

```bash
# Generate index in current directory
cd /srv/salt-repo
salt-bundle index

# Generate for specific directory
salt-bundle index /path/to/repo

# With base URL (absolute URLs)
salt-bundle index --base-url https://formulas.example.com/

# Output to different directory
salt-bundle index /srv/packages --output-dir /srv/repo
```

**Output:**
- `index.yaml` with all package versions

**Behavior:**
- Scans directory for `.tgz` files
- Reads metadata from each archive
- Calculates SHA256 digests
- Merges with existing `index.yaml` (if present)
- Sorts versions (newest first)

### add-repo

Add repository to global user configuration.

```bash
salt-bundle add-repo --name NAME --url URL
```

**Options:**

| Option        | Description                |
|---------------|----------------------------|
| `--name NAME` | Repository name (required) |
| `--url URL`   | Repository URL (required)  |

**Examples:**

```bash
# Add HTTPS repository
salt-bundle add-repo \
  --name prod \
  --url https://salt-formulas.example.com/

# Add local repository
salt-bundle add-repo \
  --name local \
  --url file:///srv/salt-repo/

# Add HTTP repository
salt-bundle add-repo \
  --name dev \
  --url http://localhost:8080/
```

**Configuration file:**
- `~/.config/salt-bundle/config.yaml`

**Format:**

```yaml
repositories:
  - name: prod
    url: https://salt-formulas.example.com/
  - name: local
    url: file:///srv/salt-repo/
```

### install

Install project dependencies.

```bash
salt-bundle install [OPTIONS]
```

**Options:**

| Option          | Description                                      |
|-----------------|--------------------------------------------------|
| `--no-lock`     | Ignore lock file and re-resolve dependencies     |
| `--update-lock` | Update lock file with latest compatible versions |

**Examples:**

```bash
# Install from lock file (or create if missing)
salt-bundle install

# Ignore lock file, re-resolve dependencies
salt-bundle install --no-lock

# Update to latest compatible versions
salt-bundle install --update-lock

# Install in different directory
salt-bundle --project-dir /path/to/project install
```

**Behavior:**

1. **With lock file** (default):
   - Installs exact versions from `salt-bundle.lock`
   - No dependency resolution

2. **Without lock file** or `--no-lock`:
   - Reads `.saltbundle.yaml`
   - Resolves dependencies
   - Creates `salt-bundle.lock`

3. **With `--update-lock`**:
   - Re-resolves dependencies
   - Updates `salt-bundle.lock`
   - Installs new versions

**Requirements:**
- `.saltbundle.yaml` must exist
- At least one repository configured

**Output:**
- Installs packages to `vendor/` directory
- Creates/updates `salt-bundle.lock`

### vendor

Install dependencies from lock file (reproducible deploy).

```bash
salt-bundle vendor
```

**Examples:**

```bash
# Install from lock file
salt-bundle vendor
```

**Behavior:**
- Identical to `salt-bundle install` without options
- Only uses `salt-bundle.lock`
- No dependency resolution

**Use case:**
- Production deployments
- CI/CD pipelines
- Reproducible builds

### verify

Verify project dependencies integrity.

```bash
salt-bundle verify
```

**Examples:**

```bash
# Verify all dependencies
salt-bundle verify

# Verify in specific directory
salt-bundle --project-dir /path/to/project verify
```

**Checks:**
- All packages from lock file are installed
- `.saltbundle.yaml` exists in each package
- Package versions match lock file

**Exit codes:**
- `0` - All dependencies verified
- `1` - Errors found

### release

Release formulas to repository (automated packaging and publishing).

```bash
salt-bundle release --formulas-dir PATH --provider PROVIDER [OPTIONS]
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
salt-bundle release \
  --formulas-dir . \
  --provider local \
  --pkg-storage-dir /srv/salt-repo

# Local provider - single formula
cd my-formula
salt-bundle release \
  --formulas-dir . \
  --single \
  --provider local \
  --pkg-storage-dir /srv/salt-repo

# GitHub provider - multiple formulas
export GITHUB_TOKEN=ghp_xxxx
export GITHUB_REPOSITORY=owner/repo
cd formulas/
salt-bundle release \
  --formulas-dir . \
  --provider github

# GitHub provider - single formula
cd my-formula
export GITHUB_TOKEN=ghp_xxxx
export GITHUB_REPOSITORY=owner/repo
salt-bundle release \
  --formulas-dir . \
  --single \
  --provider github

# Custom index branch
salt-bundle release \
  --formulas-dir . \
  --provider github \
  --index-branch main

# Dry run mode
salt-bundle release \
  --formulas-dir . \
  --provider local \
  --pkg-storage-dir /tmp/test \
  --dry-run

# Skip packaging (use existing .tgz)
salt-bundle release \
  --formulas-dir . \
  --provider local \
  --pkg-storage-dir /srv/repo \
  --skip-packaging
```

**Behavior:**

1. **Discovery**
   - Scans `formulas-dir` for formulas
   - `--single`: Treats directory as one formula
   - Default: Scans subdirectories

2. **Version Check**
   - Loads existing repository index
   - Checks which versions are new
   - Skips already published versions

3. **Packaging** (unless `--skip-packaging`)
   - Packs new formula versions
   - Validates metadata

4. **Publishing**
   - **Local**: Copies to `pkg-storage-dir`
   - **GitHub**: Creates Release, uploads asset

5. **Index Update**
   - Updates `index.yaml`
   - **Local**: Saves to `pkg-storage-dir`
   - **GitHub**: Commits to `index-branch`

**Output:**
- Summary of released packages
- Errors if any

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error occurred |

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
salt-bundle release --provider github ...
```

### GITHUB_REPOSITORY

GitHub repository in format `owner/repo`.

**Usage:**

```bash
export GITHUB_REPOSITORY=myorg/salt-formulas
salt-bundle release --provider github ...
```

## Configuration Files

### Project: .saltbundle.yaml

Location: Project root

See [Project Configuration](project-configuration.md).

### Formula: .saltbundle.yaml

Location: Formula root

See [Formula Configuration](formula-configuration.md).

### Lock File: salt-bundle.lock

Location: Project root (generated)

Format:

```yaml
dependencies:
  package-name:
    version: 1.2.3
    repository: repo-name
    url: https://example.com/package-1.2.3.tgz
    digest: sha256:abc123...
```

### User Config: ~/.config/salt-bundle/config.yaml

Global user configuration.

Format:

```yaml
repositories:
  - name: main
    url: https://formulas.example.com/
  - name: local
    url: file:///srv/salt-repo/

allowed_repos: []  # Optional security constraint
```

### Repository Index: index.yaml

Location: Repository root

See [File Formats](file-formats.md).

## Common Workflows

### Publishing Workflow

```bash
# 1. Create/edit formula
cd my-formula
vim .saltbundle.yaml  # Update version

# 2. Pack
salt-bundle pack

# 3. Copy to repository
cp my-formula-1.0.0.tgz /srv/salt-repo/

# 4. Update index
cd /srv/salt-repo
salt-bundle index
```

Or use `release` command:

```bash
cd my-formula
salt-bundle release \
  --formulas-dir . \
  --single \
  --provider local \
  --pkg-storage-dir /srv/salt-repo
```

### Installation Workflow

```bash
# 1. Create project
mkdir my-project
cd my-project
salt-bundle init --project

# 2. Add repository
salt-bundle add-repo --name main --url https://formulas.example.com/

# 3. Edit dependencies
vim .saltbundle.yaml

# 4. Install
salt-bundle install

# 5. Verify
salt-bundle verify
```

### Update Workflow

```bash
# 1. Update to latest versions
salt-bundle install --update-lock

# 2. Test
./test.sh

# 3. Commit if successful
git add salt-bundle.lock
git commit -m "Update dependencies"
```

## Debugging

### Enable Debug Mode

```bash
salt-bundle --debug install
```

**Output includes:**
- HTTP requests/responses
- File operations
- Dependency resolution details
- Stack traces on errors

### Quiet Mode

```bash
salt-bundle --quiet install
```

Suppresses all output except errors.

### Check Version

```bash
salt-bundle --version
```

## Tips and Tricks

### Batch Operations

```bash
# Install for multiple projects
for project in proj1 proj2 proj3; do
    salt-bundle --project-dir "$project" install
done

# Update all projects
for project in */; do
    cd "$project"
    salt-bundle install --update-lock
    cd ..
done
```

### Scripting

```bash
#!/bin/bash
set -e

# Exit on errors
salt-bundle install || {
    echo "Installation failed"
    exit 1
}

# Continue with deployment
echo "Deployment successful"
```

### Check Repository

```bash
# Download and view index
curl https://formulas.example.com/index.yaml | less

# Check specific package versions
curl -s https://formulas.example.com/index.yaml | \
  yq '.packages.nginx[].version'
```

## Next Steps

- [Installation Guide](installation-guide.md) - Using CLI for installation
- [Publishing Guide](publishing-guide.md) - Using CLI for publishing
- [Project Configuration](project-configuration.md) - Configuration reference
- [Formula Configuration](formula-configuration.md) - Formula metadata
