"""Install dependencies from lock file (alias for install)."""

import sys

import click


@click.command()
@click.pass_context
def vendor(ctx):
    """Install dependencies from lock file (reproducible deploy).

    This command is an alias for 'salt-bundle project install'.

    It installs formula dependencies exactly as specified in the lock file,
    ensuring reproducible deployments across different environments.

    Workflow:
    - Reads .salt-dependencies.lock for exact versions
    - Downloads and installs packages to vendor directory
    - Syncs Salt extensions automatically

    This is the recommended command for:
    - Production deployments
    - CI/CD pipelines
    - Team collaboration (shared lock file)
    - Ensuring consistent environments

    Exit codes:
    - 0: Installation successful
    - 1: Error occurred (missing lock file, download failure, etc.)

    Examples:

        # Install from lock file
        salt-bundle project vendor

        # Install in specific project directory
        salt-bundle project vendor -C /path/to/project

    See also:
    - 'salt-bundle project install' (identical behavior)
    - 'salt-bundle project update' to update dependencies
    """
    try:
        # Import and invoke install command
        from .install import install
        ctx.invoke(install)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
