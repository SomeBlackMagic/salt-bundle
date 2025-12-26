"""Install project dependencies from lock file."""

import subprocess
import sys

import click

from salt_bundle import config, lockfile, repository, vendor
from salt_bundle.utils.dependency import parse_dependency_name


@click.command()
@click.pass_context
def install(ctx):
    """Install project dependencies from lock file.

    Installs formula dependencies exactly as specified in .salt-dependencies.lock,
    ensuring reproducible deployments. If no lock file exists, reports an error.

    This command:
    - Reads locked versions from .salt-dependencies.lock
    - Downloads packages from configured repositories
    - Installs them to the vendor directory
    - Syncs Salt extensions automatically

    Lock file workflow:
    - Lock file is created by 'salt-bundle project update'
    - This command uses existing lock file without resolving dependencies
    - Guarantees same versions across different environments

    Exit codes:
    - 0: Installation successful
    - 1: Error occurred (missing lock file, download failure, etc.)

    Examples:

        # Install from lock file
        salt-bundle project install

        # Install in specific project directory
        salt-bundle project install -C /path/to/project

    See also:
    - 'salt-bundle project update' to resolve and update dependencies
    - 'salt-bundle project vendor' (alias for install)
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

        # Check if lock file exists
        lock_file_exists = lockfile.lockfile_exists(project_dir)

        if not lock_file_exists:
            click.echo("Error: .salt-dependencies.lock not found.", err=True)
            click.echo("Run 'salt-bundle project update' first to create the lock file.", err=True)
            sys.exit(1)

        # Install from lock file
        click.echo("Installing from lock file...")
        lock = lockfile.load_lockfile(project_dir)

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
