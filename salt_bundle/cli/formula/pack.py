"""Package Salt formula into distributable archive."""

import sys
from pathlib import Path

import click

from salt_bundle import package


@click.command()
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for the package archive (default: current directory)')
@click.pass_context
def pack(ctx, output_dir):
    """Package a Salt formula into a tar.gz archive.

    Reads formula metadata from .saltbundle.yaml and creates a compressed
    archive suitable for distribution. The archive includes all formula files
    and can be published to a repository.

    The output filename follows the pattern: {formula-name}-{version}.tar.gz

    Examples:

        # Package formula in current directory
        salt-bundle formula pack

        # Package and save to specific directory
        salt-bundle formula pack --output-dir /path/to/output

        # Package formula in different directory
        salt-bundle formula pack -C /path/to/formula
    """
    try:
        project_dir = ctx.obj['PROJECT_DIR']
        output_path = Path(output_dir) if output_dir else project_dir
        archive_path = package.pack_formula(project_dir, output_path)
        click.echo(f"Created package: {archive_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
