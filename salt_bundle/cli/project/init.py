"""Initialize Salt project configuration."""

import sys

import click

from salt_bundle.dependencies.saltfile import save_saltfile
from salt_bundle.dependencies.saltfile_models import SaltfileConfig


@click.command()
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.pass_context
def init(ctx, force):
    """Initialize a new Salt project with dependency management.

    Creates a Saltfile configuration file for managing
    formula dependencies, repositories, and vendoring settings.

    The project configuration includes:
    - Project name and version
    - Vendor directory location (default: vendor/)
    - Repository sources for formulas
    - Formula dependencies

    After initialization, use:
    - 'salt-bundle repo add' to add formula repositories
    - Edit Saltfile to add package dependencies
    - 'salt-bundle project install' to install dependencies

    Examples:

        # Initialize a new project interactively
        salt-bundle project init

        # Force overwrite existing configuration
        salt-bundle project init --force

        # Initialize in specific directory
        salt-bundle project init -C /path/to/project
    """
    project_dir = ctx.obj['PROJECT_DIR']
    config_file = project_dir / 'Saltfile'

    if config_file.exists() and not force:
        click.echo(f"Error: {config_file} already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

    project_config = SaltfileConfig(vendor_dir="vendor")
    save_saltfile(project_config, project_dir)
    click.echo(f"Created Saltfile: {config_file}")
    click.echo("\nNext steps:")
    click.echo("  1. Add dependencies to Saltfile")
    click.echo("     Each source must point to a repository containing index.yaml")
    click.echo("  3. Install dependencies: salt-bundle project install")
