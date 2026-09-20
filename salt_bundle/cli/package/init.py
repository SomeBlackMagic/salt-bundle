"""Initialize Salt package configuration."""

import sys

import click

from salt_bundle.packaging.extensions import ExtensionMeta
from salt_bundle.packaging.metadata import save_extension_meta, save_formula_meta
from salt_bundle.packaging.models import PackageMeta


@click.command()
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.option('--type', 'package_type', type=click.Choice(['formula', 'extension']), default='formula')
@click.pass_context
def init(ctx, force, package_type):
    """Initialize a new Salt package.

    Creates a FORMULA or EXTENSION configuration file with package metadata including:
    - Package name and version
    - Description
    - Salt version compatibility constraints

    The package configuration is used for packaging and dependency management.

    Examples:

        # Initialize a new package interactively
        salt-bundle package init

        # Force overwrite existing configuration
        salt-bundle package init --force
    """
    project_dir = ctx.obj['PROJECT_DIR']
    config_file = project_dir / ('FORMULA' if package_type == 'formula' else 'EXTENSION')

    if config_file.exists() and not force:
        click.echo(f"Error: {config_file} already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

    name = click.prompt("Package name")
    version = click.prompt("Version", default="1.0.0")
    description = click.prompt("Description", default="")

    # Salt compatibility
    salt_min = click.prompt("Salt min version", default="", show_default=False)
    salt_max = click.prompt("Salt max version", default="", show_default=False)

    metadata_kwargs = {
        'name': name,
        'version': version,
        'description': description if description else None,
        'minimum_version': salt_min if salt_min else None,
        'maximum_version': salt_max if salt_max else None,
    }
    if package_type == 'formula':
        save_formula_meta(PackageMeta(**metadata_kwargs), project_dir)
    else:
        save_extension_meta(ExtensionMeta(**metadata_kwargs), project_dir)
    click.echo(f"Created {package_type} configuration: {config_file}")
