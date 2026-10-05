"""Resolve dependencies declared in Saltfile."""

import subprocess
import sys
from pathlib import Path

import click

from salt_bundle.config import load_user_config
from salt_bundle.dependencies import lockfile, resolver
from salt_bundle.dependencies.index import download_package, fetch_index
from salt_bundle.dependencies.path_source import (
    build_index_entry_from_path,
    build_index_from_directory,
    install_from_path_link,
    install_from_path_snapshot,
    is_path_source,
    resolve_source_path,
)
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
        path_source_repositories = {
            repository.url
            for repository in user_repositories
            if repository.type == "path-source"
        }
        indexes: dict[str, object] = {}
        pending = [
            (dependency.name, dependency.version or ">=0.0.0", dependency.source, None, dependency.link)
            for dependency in saltfile.dependencies
        ]
        resolved_packages = {}
        lock = lockfile.LockFile()

        click.echo("Resolving dependencies...")
        while pending:
            package_name, constraint, source, parent_type, link = pending.pop(0)
            if package_name in resolved_packages:
                continue

            sources = [source] if source else [item.url for item in user_repositories]
            if not sources:
                click.echo(f"Error: No index.yaml source configured for {package_name}", err=True)
                sys.exit(1)

            resolved_entry = None
            resolved_source = None
            resolved_path = None
            for candidate_source in sources:
                if candidate_source in path_source_repositories:
                    try:
                        index = build_index_from_directory(Path(candidate_source))
                    except Exception as error:
                        click.echo(f"Warning: Failed to scan path source {candidate_source}: {error}", err=True)
                        continue
                    if package_name not in index.packages:
                        continue
                    candidate = resolver.resolve_version(constraint, index.packages[package_name])
                    if candidate is None:
                        continue
                    resolved_entry = candidate
                    resolved_source = candidate_source
                    resolved_path = Path(candidate.url)
                    break
                if is_path_source(candidate_source):
                    try:
                        source_dir = resolve_source_path(candidate_source, project_dir)
                        candidate = build_index_entry_from_path(source_dir)
                    except Exception as error:
                        click.echo(f"Error: {error}", err=True)
                        sys.exit(1)
                    if candidate.version != constraint and constraint != ">=0.0.0":
                        continue
                    if candidate.type == "formula" and parent_type == "extension":
                        continue
                    resolved_entry = candidate
                    resolved_source = candidate_source
                    resolved_path = source_dir
                    break
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
                "linked" if resolved_path and link else resolved_entry.digest,
                package_type=resolved_entry.type,
                dependencies={
                    dependency.name: dependency.version or ">=0.0.0"
                    for dependency in resolved_entry.dependencies
                },
                source_type="path" if resolved_path else "index",
                source_path=str(resolved_path) if resolved_path else None,
                linked=link if resolved_path else False,
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
                        False,
                    )
                )

        lockfile.save_lockfile(lock, project_dir)
        click.echo(f"Lock file updated: {project_dir / 'Saltfile.lock'}")
        for package_name, locked_dependency in lock.dependencies.items():
            click.echo(f"Installing {package_name} {locked_dependency.version}...")
            if locked_dependency.source_type == "path":
                source_dir = Path(locked_dependency.source_path or "")
                if locked_dependency.linked:
                    install_from_path_link(source_dir, package_name, vendor_dir)
                else:
                    install_from_path_snapshot(source_dir, package_name, vendor_dir)
            else:
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
