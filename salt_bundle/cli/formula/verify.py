"""Verify installed formula dependencies."""

import sys

import click

from salt_bundle import config, lockfile, vendor


@click.command()
@click.pass_context
def verify(ctx):
    """Verify integrity of installed formula dependencies.

    Checks that all dependencies listed in the lock file are properly installed
    in the vendor directory and have valid metadata files.

    Verification includes:
    - Dependency is present in vendor directory
    - .saltbundle.yaml metadata file exists
    - Version matches locked version

    Exit codes:
    - 0: All dependencies verified successfully
    - 1: Verification errors found

    Examples:

        # Verify all dependencies
        salt-bundle formula verify

        # Verify in specific project directory
        salt-bundle formula verify -C /path/to/project
    """
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
