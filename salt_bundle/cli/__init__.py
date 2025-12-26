"""CLI interface for salt-bundle."""

import sys
from pathlib import Path

import click

# Handle both package import and direct execution
try:
    from .formula import init as formula_init_cmd
    from .formula import pack as formula_pack_cmd
    from .formula import verify as formula_verify_cmd
    from .formula import sync as formula_sync_cmd
    from .project import init as project_init_cmd
    from .project import install as project_install_cmd
    from .project import update as project_update_cmd
    from .project import vendor as project_vendor_cmd
    from .repo import add as repo_add_cmd
    from .repo import index as repo_index_cmd
    from .repo import release as repo_release_cmd
except ImportError:
    # Direct execution - add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from salt_bundle.cli.formula import init as formula_init_cmd
    from salt_bundle.cli.formula import pack as formula_pack_cmd
    from salt_bundle.cli.formula import verify as formula_verify_cmd
    from salt_bundle.cli.formula import sync as formula_sync_cmd
    from salt_bundle.cli.project import init as project_init_cmd
    from salt_bundle.cli.project import install as project_install_cmd
    from salt_bundle.cli.project import update as project_update_cmd
    from salt_bundle.cli.project import vendor as project_vendor_cmd
    from salt_bundle.cli.repo import add as repo_add_cmd
    from salt_bundle.cli.repo import index as repo_index_cmd
    from salt_bundle.cli.repo import release as repo_release_cmd


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--quiet', is_flag=True, help='Suppress output')
@click.option('--project-dir', '-C', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Project directory (default: current directory)')
@click.pass_context
def cli(ctx, debug, quiet, project_dir):
    """Salt package manager - manage formulas, projects, and repositories."""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['QUIET'] = quiet
    ctx.obj['PROJECT_DIR'] = Path(project_dir) if project_dir else Path.cwd()


@cli.group()
def formula():
    """Manage Salt formulas - initialize, package, verify, and sync."""
    pass


@cli.group()
def project():
    """Manage Salt projects - dependencies, installation, and updates."""
    pass


@cli.group()
def repo():
    """Manage Salt repositories - add sources, build index, and publish releases."""
    pass


# Register formula commands
formula.add_command(formula_init_cmd.init)
formula.add_command(formula_pack_cmd.pack)
formula.add_command(formula_verify_cmd.verify)
formula.add_command(formula_sync_cmd.sync)

# Register project commands
project.add_command(project_init_cmd.init)
project.add_command(project_install_cmd.install)
project.add_command(project_update_cmd.update)
project.add_command(project_vendor_cmd.vendor)

# Register repo commands
repo.add_command(repo_add_cmd.add)
repo.add_command(repo_index_cmd.index)
repo.add_command(repo_release_cmd.release)


def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
