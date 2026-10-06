"""Generate index.html from index.yaml."""

import sys
from pathlib import Path

import click
import yaml

from salt_bundle.dependencies.index_models import Index
from salt_bundle.storage.index_html import render_index_html


@click.command('index-html')
@click.argument('index-yaml', type=click.Path(exists=True, dir_okay=False), default='index.yaml')
@click.option('--output', '-o', type=click.Path(dir_okay=False),
              help='Output path for index.html (default: next to index.yaml)')
@click.pass_context
def index_html(ctx, index_yaml, output):
    """Generate index.html from an existing index.yaml.

    Reads the package index and renders a static HTML page listing all
    packages and their versions.

    Examples:

        # Generate index.html next to index.yaml
        salt-bundle repo index-html index.yaml

        # Write to a specific file
        salt-bundle repo index-html index.yaml -o /var/www/repo/index.html
    """
    try:
        index_path = Path(index_yaml)
        data = yaml.safe_load(index_path.read_text(encoding='utf-8'))
        index = Index(**data)

        html = render_index_html(index)

        if output:
            out_path = Path(output)
        else:
            out_path = index_path.parent / 'index.html'

        out_path.write_text(html, encoding='utf-8')
        click.echo(f"Generated {out_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)
