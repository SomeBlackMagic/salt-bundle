"""Generate or update repository index."""

import sys
from pathlib import Path

import click

from salt_bundle import repository


@click.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for index.yaml (default: same as input directory)')
@click.option('--base-url', '-u',
              help='Base URL for package links in index (e.g., https://example.com/repo/)')
@click.pass_context
def index(ctx, directory, output_dir, base_url):
    """Generate or update repository index from formula packages.

    Scans a directory for formula packages (*.tar.gz files) and creates
    an index.yaml file listing all available packages and versions.

    The index.yaml format:
    - Lists all packages by name
    - Includes version, URL, digest for each package
    - Used by 'salt-bundle project update' to resolve dependencies

    Directory structure example:
        repo/
        ├── index.yaml
        ├── package-1-1.0.0.tar.gz
        ├── package-1-1.1.0.tar.gz
        └── package-2-0.5.0.tar.gz

    The --base-url option creates absolute URLs in the index, useful for
    remote repositories or CDN hosting.

    Examples:

        # Generate index in current directory
        salt-bundle repo index

        # Generate index for specific directory
        salt-bundle repo index /path/to/packages

        # Save index to different location
        salt-bundle repo index ./packages --output-dir ./public

        # Include base URL for remote access
        salt-bundle repo index . --base-url https://formulas.example.com/repo/

    See also:
    - 'salt-bundle repo release' to automate packaging and indexing
    - 'salt-bundle formula pack' to create package archives
    """
    try:
        repo_dir = Path(directory)
        output_path = Path(output_dir) if output_dir else repo_dir

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        idx = repository.generate_index(repo_dir, base_url=base_url)
        repository.save_index(idx, output_path)

        click.echo(f"Generated index with {len(idx.packages)} packages")
        for name, entries in idx.packages.items():
            click.echo(f"  {name}: {len(entries)} versions")

        if output_path != repo_dir:
            click.echo(f"Index saved to: {output_path / 'index.yaml'}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
