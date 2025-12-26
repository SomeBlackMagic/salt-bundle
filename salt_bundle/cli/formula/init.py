"""Initialize Salt formula configuration."""

import sys
from pathlib import Path

import click

from salt_bundle import config
from salt_bundle.models.package_models import PackageMeta, SaltCompatibility


@click.command()
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.pass_context
def init(ctx, force):
    """Initialize a new Salt formula.

    Creates a .saltbundle.yaml configuration file with formula metadata including:
    - Formula name and version
    - Description
    - Salt version compatibility constraints

    The formula configuration is used for packaging and dependency management.

    Examples:

        # Initialize a new formula interactively
        salt-bundle formula init

        # Force overwrite existing configuration
        salt-bundle formula init --force
    """
    project_dir = ctx.obj['PROJECT_DIR']
    config_file = project_dir / '.saltbundle.yaml'

    if config_file.exists() and not force:
        click.echo(f"Error: {config_file} already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

    name = click.prompt("Formula name")
    version = click.prompt("Version", default="1.0.0")
    description = click.prompt("Description", default="")

    # Salt compatibility
    salt_min = click.prompt("Salt min version", default="", show_default=False)
    salt_max = click.prompt("Salt max version", default="", show_default=False)

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
