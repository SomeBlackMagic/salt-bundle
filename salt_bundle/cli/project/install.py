"""Install dependencies from Saltfile.lock."""

import sys

import click

from salt_bundle.dependencies import lockfile
from salt_bundle.dependencies.index import download_package
from salt_bundle.dependencies.saltfile import load_saltfile
from salt_bundle.storage import vendor
from .update import _sync_salt_extensions


@click.command()
@click.pass_context
def install(ctx):
    """Install exactly the packages pinned in Saltfile.lock."""
    try:
        project_dir = ctx.obj["PROJECT_DIR"]
        try:
            saltfile = load_saltfile(project_dir)
        except FileNotFoundError:
            click.echo("Error: Saltfile not found. Run 'salt-bundle project init' first.", err=True)
            sys.exit(1)
        if not lockfile.lockfile_exists(project_dir):
            click.echo("Error: Saltfile.lock not found.", err=True)
            click.echo("Run 'salt-bundle project update' first to create the lock file.", err=True)
            sys.exit(1)

        vendor_dir = vendor.get_vendor_dir(project_dir, saltfile.vendor_dir)
        vendor.ensure_vendor_dir(vendor_dir)
        lock = lockfile.load_lockfile(project_dir)
        click.echo("Installing from Saltfile.lock...")
        for package_name, locked_dependency in lock.dependencies.items():
            click.echo(f"Installing {package_name} {locked_dependency.version}...")
            archive_path = download_package(
                locked_dependency.url,
                locked_dependency.repository,
                locked_dependency.digest,
            )
            vendor.install_package_to_vendor(archive_path, package_name, vendor_dir)

        _sync_salt_extensions()
        click.echo("Installation complete!")
    except Exception as error:
        click.echo(f"Error: {error}", err=True)
        if ctx.obj.get("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)
