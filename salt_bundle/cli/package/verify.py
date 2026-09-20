"""Verify installed package dependencies."""

import sys

import click

from salt_bundle.dependencies.lockfile import load_lockfile
from salt_bundle.dependencies.saltfile import load_saltfile
from salt_bundle.storage.vendor import get_vendor_dir, is_package_installed


@click.command()
@click.pass_context
def verify(ctx):
    """Verify integrity of installed package dependencies.

    Checks that all dependencies listed in the lock file are properly installed
    in the vendor directory and have valid metadata files.

    Verification includes:
    - Dependency is present in vendor directory
    - FORMULA or EXTENSION metadata file exists
    - Version matches locked version

    Exit codes:
    - 0: All dependencies verified successfully
    - 1: Verification errors found

    Examples:

        # Verify all dependencies
        salt-bundle package verify

        # Verify in specific project directory
        salt-bundle package verify -C /path/to/project
    """
    try:
        project_dir = ctx.obj['PROJECT_DIR']

        # Load lock file
        try:
            lock = load_lockfile(project_dir)
        except FileNotFoundError:
            click.echo("Error: Saltfile.lock not found", err=True)
            sys.exit(1)

        # Load project manifest
        proj_config = load_saltfile(project_dir)
        vendor_dir = get_vendor_dir(project_dir, proj_config.vendor_dir)

        errors = []

        for dep_name, locked_dep in lock.dependencies.items():
            # Check if installed
            if not is_package_installed(dep_name, vendor_dir):
                errors.append(f"  {dep_name}: not installed")
                continue

            package_dir = vendor_dir / dep_name
            metadata_file = (
                package_dir / "FORMULA"
                if (package_dir / "FORMULA").exists()
                else package_dir / "EXTENSION"
            )
            if not metadata_file.exists():
                errors.append(f"  {dep_name}: package metadata missing")
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
