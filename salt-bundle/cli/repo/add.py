"""Add repository to configuration."""

import sys

import click

from salt_bundle import config


@click.command()
@click.option('--name', required=True, help='Repository name (unique identifier)')
@click.option('--url', required=True, help='Repository URL (must contain index.yaml)')
@click.pass_context
def add(ctx, name, url):
    """Add a formula repository to project or global configuration.

    Repositories provide access to formula packages via an index.yaml file.
    When a .salt-dependencies.yaml exists in the current directory, the
    repository is added to the project configuration. Otherwise, it's added
    to the global user configuration (~/.salt-bundle/config.yaml).

    Repository types:
    - HTTP/HTTPS: Remote repositories (e.g., https://example.com/repo/)
    - File: Local directories (e.g., file:///path/to/repo/)
    - GitHub Pages: Static hosting for formula repositories

    The URL should point to a directory containing index.yaml.

    Examples:

        # Add remote repository to project
        salt-bundle repo add --name official --url https://formulas.example.com/

        # Add local repository
        salt-bundle repo add --name local --url file:///opt/formulas/

        # Add to global configuration (no project found)
        cd /tmp
        salt-bundle repo add --name global --url https://repo.example.com/

    See also:
    - 'salt-bundle repo index' to create repository index
    - 'salt-bundle project update' to install from repositories
    """
    try:
        project_dir = ctx.obj['PROJECT_DIR']
        local_config_file = project_dir / '.salt-dependencies.yaml'

        # Check if local project config exists
        if local_config_file.exists():
            # Add to project configuration
            config.add_project_repository(name, url, project_dir)
            click.echo(f"Added repository to project: {name} -> {url}")
        else:
            # Add to global user configuration
            config.add_user_repository(name, url)
            click.echo(f"Added repository globally: {name} -> {url}")
            click.echo(f"Note: No .salt-dependencies.yaml found in current directory, added to user config")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
