"""Package Salt package into distributable archive."""

import sys
from pathlib import Path

import click

from salt_bundle.packaging.archives import pack_package


@click.command()
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for the package archive (default: current directory)')
@click.pass_context
def pack(ctx, output_dir):
    """Package a Salt package into a tar.gz archive.

    Reads package metadata from FORMULA or EXTENSION and creates a compressed
    archive suitable for distribution. The archive includes all package files
    and can be published to a repository.

    The output filename follows the pattern: {formula-name}-{version}.tar.gz

    Examples:

        # Package the current directory
        salt-bundle package pack

        # Package and save to specific directory
        salt-bundle package pack --output-dir /path/to/output

        # Package a different directory
        salt-bundle package pack -C /path/to/package
    """
    try:
        project_dir = ctx.obj['PROJECT_DIR']
        output_path = Path(output_dir) if output_dir else project_dir
        archive_path = pack_package(project_dir, output_path)
        click.echo(f"Created package: {archive_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
