"""Resolve and update project dependencies."""

import subprocess
import sys

import click

from salt_bundle import config, lockfile, repository, resolver, vendor
from salt_bundle.utils.dependency import parse_dependency_name


@click.command()
@click.pass_context
def update(ctx):
    """Resolve dependencies and update lock file.

    Resolves all formula dependencies from .salt-dependencies.yaml by:
    - Querying configured repositories for available versions
    - Selecting versions that satisfy version constraints
    - Creating or updating .salt-dependencies.lock with resolved versions
    - Installing resolved packages to vendor directory
    - Syncing Salt extensions

    Dependency resolution:
    - Searches all configured repositories (project + user)
    - Can specify repository: "repo/package" or search all: "package"
    - Resolves version constraints (e.g., ">=1.0.0", "~1.2.0")
    - Fails if any dependency cannot be resolved

    Use this command when:
    - Adding new dependencies to .salt-dependencies.yaml
    - Updating existing dependencies to newer versions
    - Initial project setup (creates lock file)

    Exit codes:
    - 0: Dependencies resolved and installed successfully
    - 1: Resolution or installation failed

    Examples:

        # Resolve and install all dependencies
        salt-bundle project update

        # Update in specific project directory
        salt-bundle project update -C /path/to/project

    See also:
    - 'salt-bundle project install' to install from existing lock file
    - 'salt-bundle repo add' to configure repositories
    """
    try:
        project_dir = ctx.obj['PROJECT_DIR']

        # Load project config
        try:
            proj_config = config.load_project_config(project_dir)
        except FileNotFoundError:
            click.echo("Error: .salt-dependencies.yaml not found. Run 'salt-bundle project init' first.", err=True)
            sys.exit(1)

        vendor_dir = vendor.get_vendor_dir(project_dir, proj_config.vendor_dir)
        vendor.ensure_vendor_dir(vendor_dir)

        # Get all repositories (project + user)
        user_config = config.load_user_config()
        all_repos = proj_config.repositories + user_config.repositories

        if not all_repos:
            click.echo("Warning: No repositories configured", err=True)

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
        click.echo(f"\nLock file updated: {project_dir / '.salt-dependencies.lock'}")

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

        click.echo("\nDependencies updated and installed!")

        # Sync Salt extensions
        try:
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
