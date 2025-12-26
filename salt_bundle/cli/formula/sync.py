"""Sync formula modules to Salt cache."""

import shutil
import subprocess
import sys
from pathlib import Path

import click

from salt_bundle import config, vendor


@click.command()
@click.option('--cache-dir', type=click.Path(),
              help='Salt cache directory (auto-detected if not specified)')
@click.pass_context
def sync(ctx, cache_dir):
    """Sync vendor formula modules to Salt's extension modules cache.

    Copies custom modules (_modules, _states, _grains, etc.) from vendor
    formulas to Salt's extmods cache directory, making them available to Salt.

    Module types synchronized:
    - modules, states, grains, pillar, returners, runners
    - output, utils, renderers, engines, proxy, beacons

    After copying, automatically runs 'salt-call --local saltutil.sync_all'
    to register the extensions with Salt.

    Examples:

        # Auto-detect cache directory and sync
        salt-bundle formula sync

        # Specify custom cache directory
        salt-bundle formula sync --cache-dir /var/cache/salt/minion/extmods

        # Sync from different project directory
        salt-bundle formula sync -C /path/to/project
    """
    try:
        project_dir = ctx.obj['PROJECT_DIR']

        # Load project config
        proj_config = config.load_project_config(project_dir)
        vendor_dir = vendor.get_vendor_dir(project_dir, proj_config.vendor_dir)

        # Find Salt cache dir
        if not cache_dir:
            # Try to auto-detect from opts
            from salt_bundle.ext.loader import _find_project_config
            cfg_path = _find_project_config()
            if cfg_path:
                # Assume standard structure
                salt_root = cfg_path.parent
                cache_dir = salt_root / "var" / "cache" / "salt" / "minion" / "extmods"
            else:
                click.echo("Error: Could not auto-detect Salt cache directory. Use --cache-dir", err=True)
                sys.exit(1)

        cache_path = Path(cache_dir)
        click.echo(f"Syncing to: {cache_path}")

        # Module types to sync
        module_types = ['modules', 'states', 'grains', 'pillar', 'returners', 'runners',
                       'output', 'utils', 'renderers', 'engines', 'proxy', 'beacons']

        synced = []

        # Iterate through vendor formulas
        for formula_dir in vendor_dir.iterdir():
            if not formula_dir.is_dir() or formula_dir.name.startswith('.'):
                continue

            formula_name = formula_dir.name

            # Check each module type
            for mod_type in module_types:
                src_dir = formula_dir / f"_{mod_type}"
                if not src_dir.exists():
                    continue

                dst_dir = cache_path / mod_type
                dst_dir.mkdir(parents=True, exist_ok=True)

                # Copy all .py files
                for src_file in src_dir.glob("*.py"):
                    dst_file = dst_dir / src_file.name
                    shutil.copy2(src_file, dst_file)
                    synced.append(f"{mod_type}/{src_file.name} (from {formula_name})")
                    if not ctx.obj.get('QUIET'):
                        click.echo(f"  ✓ {mod_type}/{src_file.name}")

        if synced:
            click.echo(f"\nSynced {len(synced)} module(s)")
        else:
            click.echo("No modules found to sync")

        # Sync Salt extensions
        try:
            click.echo("\nSyncing Salt extensions...")
            result = subprocess.run(['salt-call', '--local', 'saltutil.sync_all'],
                                   capture_output=True, text=True, check=False)
            if result.returncode == 0:
                click.echo("✓ Salt extensions synced")
            else:
                click.echo(f"Warning: Failed to sync Salt extensions: {result.stderr}", err=True)
        except FileNotFoundError:
            click.echo("Warning: salt-call not found, skipping extension sync", err=True)
        except Exception as e:
            click.echo(f"Warning: Failed to sync Salt extensions: {e}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)
