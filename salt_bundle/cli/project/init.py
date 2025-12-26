"""Initialize Salt project configuration."""

import sys
from pathlib import Path

import click

from salt_bundle import config
from salt_bundle.models.config_models import ProjectConfig


@click.command()
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.pass_context
def init(ctx, force):
    """Initialize a new Salt project with dependency management.

    Creates a .salt-dependencies.yaml configuration file for managing
    formula dependencies, repositories, and vendoring settings.

    The project configuration includes:
    - Project name and version
    - Vendor directory location (default: vendor/)
    - Repository sources for formulas
    - Formula dependencies

    After initialization, use:
    - 'salt-bundle repo add' to add formula repositories
    - Edit .salt-dependencies.yaml to add formula dependencies
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
    config_file = project_dir / '.salt-dependencies.yaml'

    if config_file.exists() and not force:
        click.echo(f"Error: {config_file} already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

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
    click.echo("\nNext steps:")
    click.echo("  1. Add repositories: salt-bundle repo add --name <name> --url <url>")
    click.echo("  2. Add dependencies to .salt-dependencies.yaml")
    click.echo("  3. Install dependencies: salt-bundle project install")
