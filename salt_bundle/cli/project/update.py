"""Resolve dependencies declared in Saltfile."""

import subprocess
import sys

import click

from salt_bundle.config import load_user_config
from salt_bundle.dependencies import lockfile, resolver
from salt_bundle.dependencies.index import download_package, fetch_index
from salt_bundle.dependencies.saltfile import load_saltfile
from salt_bundle.storage import vendor


def _load_index(source: str, indexes: dict[str, object]) -> object:
    if source not in indexes:
        indexes[source] = fetch_index(source)
    return indexes[source]


@click.command()
@click.pass_context
def update(ctx):
    """Resolve Saltfile dependencies, write Saltfile.lock, and install packages."""
    try:
        project_dir = ctx.obj["PROJECT_DIR"]
        try:
            saltfile = load_saltfile(project_dir)
        except FileNotFoundError:
            click.echo("Error: Saltfile not found. Run 'salt-bundle project init' first.", err=True)
            sys.exit(1)

        vendor_dir = vendor.get_vendor_dir(project_dir, saltfile.vendor_dir)
        vendor.ensure_vendor_dir(vendor_dir)
        user_repositories = load_user_config().repositories
        indexes: dict[str, object] = {}
        pending = [
            (dependency.name, dependency.version or ">=0.0.0", dependency.source, None)
            for dependency in saltfile.dependencies
        ]
        resolved_packages = {}
        lock = lockfile.LockFile()

        click.echo("Resolving dependencies...")
        while pending:
            package_name, constraint, source, parent_type = pending.pop(0)
            if package_name in resolved_packages:
                continue

            sources = [source] if source else [item.url for item in user_repositories]
            if not sources:
                click.echo(f"Error: No index.yaml source configured for {package_name}", err=True)
                sys.exit(1)

            resolved_entry = None
            resolved_source = None
            for candidate_source in sources:
                try:
                    index = _load_index(candidate_source, indexes)
                except Exception as error:
                    click.echo(f"Warning: Failed to fetch index from {candidate_source}: {error}", err=True)
                    continue
                if package_name not in index.packages:
                    continue
                candidate = resolver.resolve_version(constraint, index.packages[package_name])
                if candidate is not None:
                    resolved_entry = candidate
                    resolved_source = candidate_source
                    break

            if resolved_entry is None or resolved_source is None:
                click.echo(f"Error: Could not resolve dependency: {package_name} {constraint}", err=True)
                sys.exit(1)
            if parent_type == "extension" and resolved_entry.type == "formula":
                click.echo(
                    f"Error: Extension dependency {package_name} cannot resolve to a formula",
                    err=True,
                )
                sys.exit(1)

            lockfile.add_locked_dependency(
                lock,
                package_name,
                resolved_entry.version,
                resolved_source,
                resolved_entry.url,
                resolved_entry.digest,
                package_type=resolved_entry.type,
            )
            resolved_packages[package_name] = resolved_entry
            click.echo(f"  ✓ {package_name} {resolved_entry.version} from {resolved_source}")
            for dependency in resolved_entry.dependencies:
                pending.append(
                    (
                        dependency.name,
                        dependency.version or ">=0.0.0",
                        dependency.url or resolved_source,
                        resolved_entry.type,
                    )
                )

        lockfile.save_lockfile(lock, project_dir)
        click.echo(f"Lock file updated: {project_dir / 'Saltfile.lock'}")
        for package_name, locked_dependency in lock.dependencies.items():
            click.echo(f"Installing {package_name} {locked_dependency.version}...")
            archive_path = download_package(
                locked_dependency.url,
                locked_dependency.repository,
                locked_dependency.digest,
            )
            vendor.install_package_to_vendor(archive_path, package_name, vendor_dir)

        _sync_salt_extensions()
        click.echo("Dependencies updated and installed!")
    except Exception as error:
        click.echo(f"Error: {error}", err=True)
        if ctx.obj.get("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _sync_salt_extensions() -> None:
    try:
        result = subprocess.run(
            ["salt-call", "--local", "saltutil.sync_all"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            click.echo("✓ Salt extensions synced")
        else:
            click.echo(f"Warning: Failed to sync Salt extensions: {result.stderr}", err=True)
    except FileNotFoundError:
        click.echo("Warning: salt-call not found, skipping extension sync", err=True)
