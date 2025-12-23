"""CLI interface for salt-bundle."""

import sys
from pathlib import Path

import click

# Handle both package import and direct execution
try:
    from . import config, lockfile, package, release, repository, resolver, vendor
    from .models.config_models import ProjectConfig, RepositoryConfig
    from .models.package_models import PackageMeta
    from .utils.dependency import parse_dependency_name
except ImportError:
    # Direct execution - add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from salt_bundle import config, lockfile, package, release, repository, resolver, vendor
    from salt_bundle.models.config_models import ProjectConfig, RepositoryConfig
    from salt_bundle.models.package_models import PackageMeta
    from salt_bundle.utils.dependency import parse_dependency_name


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--quiet', is_flag=True, help='Suppress output')
@click.option('--project-dir', '-C', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Project directory (default: current directory)')
@click.pass_context
def cli(ctx, debug, quiet, project_dir):
    """Salt package manager."""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['QUIET'] = quiet
    ctx.obj['PROJECT_DIR'] = Path(project_dir) if project_dir else Path.cwd()


@cli.command()
@click.option('--project', 'config_type', flag_value='project', help='Initialize project configuration')
@click.option('--formula', 'config_type', flag_value='formula', help='Initialize formula configuration')
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.pass_context
def init(ctx, config_type, force):
    """Initialize salt-bundle configuration."""
    if not config_type:
        click.echo("Error: Specify --project or --formula", err=True)
        sys.exit(1)

    project_dir = ctx.obj['PROJECT_DIR']
    config_file = project_dir / '.saltbundle.yaml'

    if config_file.exists() and not force:
        click.echo(f"Error: {config_file} already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

    if config_type == 'project':
        name = click.prompt("Project name", default="my-project")
        version = click.prompt("Version", default="0.1.0")

        project_config = ProjectConfig(
            project=name,
            version=version,
            vendor_dir="vendor",
            repositories=[],
            dependencies={}
        )

        config.save_project_config(project_config, project_dir)
        click.echo(f"Created project configuration: {config_file}")

    elif config_type == 'formula':
        name = click.prompt("Formula name")
        version = click.prompt("Version", default="1.0.0")
        description = click.prompt("Description", default="")

        # Salt compatibility
        salt_min = click.prompt("Salt min version", default="", show_default=False)
        salt_max = click.prompt("Salt max version", default="", show_default=False)

        # Import SaltCompatibility model
        from salt_bundle.models.package_models import SaltCompatibility

        salt_compat = None
        if salt_min or salt_max:
            salt_compat = SaltCompatibility(
                min_version=salt_min if salt_min else None,
                max_version=salt_max if salt_max else None
            )

        formula_meta = PackageMeta(
            name=name,
            version=version,
            description=description if description else None,
            salt=salt_compat
        )

        config.save_package_meta(formula_meta, project_dir)
        click.echo(f"Created formula configuration: {config_file}")


@cli.command()
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
@click.pass_context
def pack(ctx, output_dir):
    """Pack formula into tar.gz archive."""
    try:
        project_dir = ctx.obj['PROJECT_DIR']
        output_path = Path(output_dir) if output_dir else project_dir
        archive_path = package.pack_formula(project_dir, output_path)
        click.echo(f"Created package: {archive_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory for index.yaml (default: same as input directory)')
@click.option('--base-url', '-u', help='Base URL for package links in index (e.g., https://example.com/repo/)')
@click.pass_context
def index(ctx, directory, output_dir, base_url):
    """Generate or update repository index."""
    try:
        repo_dir = Path(directory)
        output_path = Path(output_dir) if output_dir else repo_dir

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        idx = repository.generate_index(repo_dir, base_url=base_url)
        repository.save_index(idx, output_path)

        click.echo(f"Generated index with {len(idx.packages)} packages")
        for name, entries in idx.packages.items():
            click.echo(f"  {name}: {len(entries)} versions")

        if output_path != repo_dir:
            click.echo(f"Index saved to: {output_path / 'index.yaml'}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command('add-repo')
@click.option('--name', required=True, help='Repository name')
@click.option('--url', required=True, help='Repository URL')
@click.pass_context
def add_repo(ctx, name, url):
    """Add repository to project or user configuration."""
    try:
        project_dir = ctx.obj['PROJECT_DIR']
        local_config_file = project_dir / '.salt-dependencies.yaml'

        # Check if local project config exists
        if local_config_file.exists():
            # Add to project configuration
            config.add_project_repository(name, url, project_dir)
            click.echo(f"Added repository to project: {name} -> {url}")
        else:
            # Add to global user configuration
            config.add_user_repository(name, url)
            click.echo(f"Added repository globally: {name} -> {url}")
            click.echo(f"Note: No .salt-dependencies.yaml found in current directory, added to user config")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--no-lock', is_flag=True, help='Ignore lock file')
@click.option('--update-lock', is_flag=True, help='Update lock file')
@click.pass_context
def install(ctx, no_lock, update_lock):
    """Install project dependencies."""
    try:
        project_dir = ctx.obj['PROJECT_DIR']

        # Load project config
        try:
            proj_config = config.load_project_config(project_dir)
        except FileNotFoundError:
            click.echo("Error: .salt-dependencies.yaml not found. Run 'salt-bundle init --project' first.", err=True)
            sys.exit(1)

        vendor_dir = vendor.get_vendor_dir(project_dir, proj_config.vendor_dir)
        vendor.ensure_vendor_dir(vendor_dir)

        # Get all repositories (project + user)
        user_config = config.load_user_config()
        all_repos = proj_config.repositories + user_config.repositories

        if not all_repos:
            click.echo("Warning: No repositories configured", err=True)

        # Check if we need to resolve dependencies
        lock_file_exists = lockfile.lockfile_exists(project_dir)

        if lock_file_exists and not no_lock and not update_lock:
            # Install from lock file
            click.echo("Installing from lock file...")
            lock = lockfile.load_lockfile(project_dir)
        else:
            # Resolve dependencies
            click.echo("Resolving dependencies...")
            lock = lockfile.LockFile()

            for dep_key, dep_constraint in proj_config.dependencies.items():
                # Parse dependency format: "repo/package" or "package"
                try:
                    repo_name, pkg_name = parse_dependency_name(dep_key)
                except ValueError as e:
                    click.echo(f"Error: {e}", err=True)
                    sys.exit(1)

                # Select repositories to search
                if repo_name:
                    # Use specific repository
                    repos_to_try = [r for r in all_repos if r.name == repo_name]
                    if not repos_to_try:
                        click.echo(
                            f"Error: Repository '{repo_name}' not found for dependency '{dep_key}'",
                            err=True
                        )
                        click.echo(f"Available repositories: {', '.join(r.name for r in all_repos)}")
                        sys.exit(1)
                    click.echo(f"Resolving {pkg_name} from {repo_name}...")
                else:
                    # Try all repositories
                    repos_to_try = all_repos
                    click.echo(f"Resolving {pkg_name}...")

                resolved = None

                # Try each repository
                for repo in repos_to_try:
                    try:
                        idx = repository.fetch_index(repo.url)
                        if pkg_name in idx.packages:
                            resolved_entry = resolver.resolve_version(dep_constraint, idx.packages[pkg_name])
                            if resolved_entry:
                                lockfile.add_locked_dependency(
                                    lock,
                                    pkg_name,
                                    resolved_entry.version,
                                    repo.name,
                                    resolved_entry.url,
                                    resolved_entry.digest
                                )
                                resolved = resolved_entry
                                click.echo(f"  ✓ {pkg_name} {resolved_entry.version} from {repo.name}")
                                break
                    except Exception as e:
                        if repo_name:
                            # If a specific repo is specified, this is an error
                            click.echo(f"Error: Failed to fetch from {repo.name}: {e}", err=True)
                            sys.exit(1)
                        else:
                            # If we go through everything - a warning
                            click.echo(f"Warning: Failed to fetch from {repo.name}: {e}", err=True)

                if not resolved:
                    click.echo(f"Error: Could not resolve dependency: {dep_key} {dep_constraint}", err=True)
                    sys.exit(1)

            # Save lock file
            lockfile.save_lockfile(lock, project_dir)

        # Install packages
        for dep_name, locked_dep in lock.dependencies.items():
            click.echo(f"Installing {dep_name} {locked_dep.version}...")

            # Find repository URL
            repo_url = None
            for repo in all_repos:
                if repo.name == locked_dep.repository:
                    repo_url = repo.url
                    break

            if not repo_url:
                click.echo(f"Error: Repository not found: {locked_dep.repository}", err=True)
                sys.exit(1)

            # Download package
            archive_path = repository.download_package(
                locked_dep.url,
                repo_url,
                locked_dep.digest
            )

            # Install to vendor
            vendor.install_package_to_vendor(archive_path, dep_name, vendor_dir)

        click.echo("Installation complete!")

        # Sync Salt extensions
        try:
            import subprocess
            click.echo("\nSyncing Salt extensions...")
            result = subprocess.run(['salt-call', '--local', 'saltutil.sync_all'],
                                   capture_output=True, text=True, check=False)
            if result.returncode == 0:
                click.echo("✓ Salt extensions synced")
            else:
                click.echo(f"Warning: Failed to sync Salt extensions: {result.stderr}", err=True)
        except FileNotFoundError:
            click.echo("Warning: salt-call not found, skipping extension sync", err=True)
        except Exception as e:
            click.echo(f"Warning: Failed to sync Salt extensions: {e}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.pass_context
def vendor_cmd(ctx):
    """Install dependencies from lock file (reproducible deploy)."""
    try:
        # Reuse install logic with --no-lock flag behavior
        ctx.invoke(install, no_lock=False, update_lock=False)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def verify(ctx):
    """Verify project dependencies integrity."""
    try:
        project_dir = ctx.obj['PROJECT_DIR']

        # Load lock file
        try:
            lock = lockfile.load_lockfile(project_dir)
        except FileNotFoundError:
            click.echo("Error: .salt-dependencies.lock not found", err=True)
            sys.exit(1)

        # Load project config
        proj_config = config.load_project_config(project_dir)
        vendor_dir = vendor.get_vendor_dir(project_dir, proj_config.vendor_dir)

        errors = []

        for dep_name, locked_dep in lock.dependencies.items():
            # Check if installed
            if not vendor.is_package_installed(dep_name, vendor_dir):
                errors.append(f"  {dep_name}: not installed")
                continue

            # Check .saltbundle.yaml exists
            package_meta_file = vendor_dir / dep_name / '.saltbundle.yaml'
            if not package_meta_file.exists():
                errors.append(f"  {dep_name}: .saltbundle.yaml missing")
                continue

            click.echo(f"✓ {dep_name} {locked_dep.version}")

        if errors:
            click.echo("\nErrors found:")
            for error in errors:
                click.echo(error, err=True)
            sys.exit(1)
        else:
            click.echo("\nAll dependencies verified successfully!")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--formulas-dir', '-f', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              required=True, help='Directory containing formulas (required)')
@click.option('--single', is_flag=True, help='Treat formulas-dir as a single formula directory (not subdirectories)')
@click.option('--provider', '-p', type=click.Choice(['local', 'github'], case_sensitive=False),
              required=True, help='Release provider: local (filesystem) or github (GitHub releases)')
@click.option('--pkg-storage-dir', type=click.Path(file_okay=False, dir_okay=True),
              help='[local provider] Directory where packages and index.yaml will be stored (required for local provider)')
@click.option('--index-branch', type=str, default='gh-pages',
              help='[github provider] Git branch for index.yaml (default: gh-pages)')
@click.option('--skip-packaging', is_flag=True, help='Skip packaging step (use existing .tgz files)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
@click.pass_context
def release_cmd(ctx, formulas_dir, single, provider, pkg_storage_dir, index_branch, skip_packaging, dry_run):
    """Release formulas to repository.

    This command automates the process of:
    1. Discovering formulas in the specified directory
    2. Detecting new versions (not in repository)
    3. Packaging formulas (unless --skip-packaging)
    4. Publishing to provider storage
    5. Updating repository index

    REQUIRED PARAMETERS:
    - --formulas-dir: Directory with formulas
    - --provider: Storage provider (local or github)

    PROVIDER: LOCAL
    Stores packages in local filesystem with structure:
      {pkg-storage-dir}/
        ├── index.yaml
        ├── {package-1}/
        │   └── package-1-0.1.0.tgz
        └── {package-2}/
            └── package-2-0.1.0.tgz

    Required: --pkg-storage-dir

    PROVIDER: GITHUB
    Creates GitHub releases and stores index.yaml in separate branch:
    - Packages uploaded as release assets
    - index.yaml stored in git branch (default: gh-pages)
    - Branch contains ONLY index.yaml

    Required environment variables:
    - GITHUB_TOKEN: Personal access token with repo permissions
    - GITHUB_REPOSITORY: Repository in format 'owner/repo'

    Optional: --index-branch (default: gh-pages)

    EXAMPLES:
    # Local provider
    salt-bundle release --formulas-dir ./formulas --provider local --pkg-storage-dir ./repo

    # GitHub provider
    export GITHUB_TOKEN=ghp_xxx
    export GITHUB_REPOSITORY=owner/repo
    salt-bundle release --formulas-dir ./formulas --provider github

    # Single formula
    salt-bundle release --formulas-dir ./my-formula --single --provider local --pkg-storage-dir ./repo
    """
    try:
        formulas_path = Path(formulas_dir)

        if dry_run:
            click.echo("=== DRY RUN MODE ===")

        mode = "single formula" if single else "multiple formulas"
        click.echo(f"Mode: {mode}")
        click.echo(f"Formulas directory: {formulas_path}")
        click.echo(f"Provider: {provider}")

        # Initialize provider
        from salt_bundle.providers import LocalReleaseProvider, GitHubReleaseProvider

        if provider == 'local':
            if not pkg_storage_dir:
                click.echo("Error: --pkg-storage-dir is required for local provider", err=True)
                sys.exit(1)

            storage_path = Path(pkg_storage_dir)
            click.echo(f"Storage directory: {storage_path}")
            click.echo()

            provider_instance = LocalReleaseProvider(storage_path)

        elif provider == 'github':
            import os
            token = os.getenv('GITHUB_TOKEN')
            repo = os.getenv('GITHUB_REPOSITORY')

            if not token or not repo:
                click.echo("Error: GITHUB_TOKEN and GITHUB_REPOSITORY environment variables are required", err=True)
                sys.exit(1)

            click.echo(f"GitHub repository: {repo}")
            click.echo(f"Index branch: {index_branch}")
            click.echo()

            provider_instance = GitHubReleaseProvider(
                token=token,
                repository=repo,
                index_branch=index_branch
            )

        else:
            click.echo(f"Error: Unknown provider: {provider}", err=True)
            sys.exit(1)

        # Run release process
        released, errors = release.release_formulas(
            formulas_path,
            provider_instance,
            skip_packaging=skip_packaging,
            dry_run=dry_run,
            single_formula=single,
        )

        # Summary
        click.echo()
        click.echo("=" * 50)
        click.echo("RELEASE SUMMARY")
        click.echo("=" * 50)

        if released:
            click.echo(f"\n✓ Released {len(released)} package(s):")
            for formula in released:
                click.echo(f"  - {formula.name} {formula.version}")
        else:
            click.echo("\nNo packages released")

        if errors:
            click.echo(f"\n✗ Errors ({len(errors)}):")
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        if dry_run:
            click.echo("\n[DRY RUN] No changes were made")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)




@cli.command()
@click.option('--cache-dir', type=click.Path(), help='Salt cache directory (auto-detected if not specified)')
@click.pass_context
def sync(ctx, cache_dir):
    """Sync vendor formula modules to Salt's extmods cache.

    This command copies custom modules (_modules, _states, etc.) from vendor
    formulas to Salt's extension modules cache, making them available to Salt.
    """
    import shutil

    try:
        project_dir = ctx.obj['PROJECT_DIR']

        # Load project config
        proj_config = config.load_project_config(project_dir)
        vendor_dir = vendor.get_vendor_dir(project_dir, proj_config.vendor_dir)

        # Find Salt cache dir
        if not cache_dir:
            # Try to auto-detect from opts
            from salt_bundle.ext.loader import _find_project_config
            cfg_path = _find_project_config()
            if cfg_path:
                # Assume standard structure
                salt_root = cfg_path.parent
                cache_dir = salt_root / "var" / "cache" / "salt" / "minion" / "extmods"
            else:
                click.echo("Error: Could not auto-detect Salt cache directory. Use --cache-dir", err=True)
                sys.exit(1)

        cache_path = Path(cache_dir)
        click.echo(f"Syncing to: {cache_path}")

        # Module types to sync
        module_types = ['modules', 'states', 'grains', 'pillar', 'returners', 'runners',
                       'output', 'utils', 'renderers', 'engines', 'proxy', 'beacons']

        synced = []

        # Iterate through vendor formulas
        for formula_dir in vendor_dir.iterdir():
            if not formula_dir.is_dir() or formula_dir.name.startswith('.'):
                continue

            formula_name = formula_dir.name

            # Check each module type
            for mod_type in module_types:
                src_dir = formula_dir / f"_{mod_type}"
                if not src_dir.exists():
                    continue

                dst_dir = cache_path / mod_type
                dst_dir.mkdir(parents=True, exist_ok=True)

                # Copy all .py files
                for src_file in src_dir.glob("*.py"):
                    dst_file = dst_dir / src_file.name
                    shutil.copy2(src_file, dst_file)
                    synced.append(f"{mod_type}/{src_file.name} (from {formula_name})")
                    if not ctx.obj.get('QUIET'):
                        click.echo(f"  ✓ {mod_type}/{src_file.name}")

        if synced:
            click.echo(f"\nSynced {len(synced)} module(s)")
        else:
            click.echo("No modules found to sync")

        # Sync Salt extensions
        try:
            import subprocess
            click.echo("\nSyncing Salt extensions...")
            result = subprocess.run(['salt-call', '--local', 'saltutil.sync_all'],
                                   capture_output=True, text=True, check=False)
            if result.returncode == 0:
                click.echo("✓ Salt extensions synced")
            else:
                click.echo(f"Warning: Failed to sync Salt extensions: {result.stderr}", err=True)
        except FileNotFoundError:
            click.echo("Warning: salt-call not found, skipping extension sync", err=True)
        except Exception as e:
            click.echo(f"Warning: Failed to sync Salt extensions: {e}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
