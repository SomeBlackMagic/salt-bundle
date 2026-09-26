"""Commands for inspecting target-aware package activation."""

from pathlib import Path

import click

from salt_bundle.activation.errors import ActivationError
from salt_bundle.activation.matcher import collect_packages, find_matching_rules
from salt_bundle.activation.parser import load_top_bundle
from salt_bundle.activation.resolver import ActivationResolver
from salt_bundle.dependencies.lockfile import load_lockfile
from salt_bundle.dependencies.saltfile import load_saltfile
from salt_bundle.storage.vendor import get_vendor_dir


def _resolver(project_dir: Path) -> ActivationResolver:
    config = load_saltfile(project_dir)
    return ActivationResolver(
        top_bundle=load_top_bundle(project_dir / "top_bundle.sls"),
        lock_data=load_lockfile(project_dir),
        vendor_root=get_vendor_dir(project_dir, config.vendor_dir),
    )


def _fail(error: Exception) -> None:
    raise click.ClickException(str(error)) from error


@click.group()
def runtime() -> None:
    """Inspect target-specific runtime package activation."""


@runtime.command()
@click.argument("target")
@click.option("--saltenv", default="base", show_default=True)
@click.pass_context
def resolve(ctx: click.Context, target: str, saltenv: str) -> None:
    """Display packages active for TARGET."""
    try:
        active_set = _resolver(ctx.obj["PROJECT_DIR"]).resolve(target, saltenv=saltenv)
    except (ActivationError, OSError, ValueError) as error:
        _fail(error)
    click.echo(f"Target: {target}")
    click.echo(f"Environment: {saltenv}")
    click.echo(f"Fingerprint: sha256:{active_set.fingerprint}")
    click.echo("\nPackages:")
    for package in active_set.packages:
        click.echo(f"  {package.name} {package.version}")


@runtime.command()
@click.argument("target")
@click.option("--saltenv", default="base", show_default=True)
@click.pass_context
def explain(ctx: click.Context, target: str, saltenv: str) -> None:
    """Explain why packages are active for TARGET."""
    try:
        resolver = _resolver(ctx.obj["PROJECT_DIR"])
        environment = resolver.top_bundle.environments.get(saltenv)
        rules = (
            find_matching_rules(target, environment.rules)
            if environment is not None
            else []
        )
        direct = collect_packages(rules)
        active_set = resolver.resolve(target, saltenv=saltenv)
    except (ActivationError, OSError, ValueError) as error:
        _fail(error)
    direct_names = set(direct)
    click.echo(target)
    click.echo("\nMatched:")
    for rule in rules:
        click.echo(f"  '{rule.target_expr}' -> " + ", ".join(map(str, rule.packages)))
    click.echo("\nTransitive:")
    for package in active_set.packages:
        if package.name not in direct_names:
            click.echo(f"  {package.name}")
    click.echo("\nFinal:")
    for package in active_set.packages:
        click.echo(f"  {package.name}")


@runtime.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate each package referenced by top_bundle.sls."""
    try:
        resolver = _resolver(ctx.obj["PROJECT_DIR"])
        for environment in resolver.top_bundle.environments.values():
            for rule in environment.rules:
                resolver.resolve(rule.target_expr, saltenv=environment.name)
    except (ActivationError, OSError, ValueError) as error:
        click.echo(f"Error: {error}", err=True)
        raise click.exceptions.Exit(1) from error
    click.echo("Runtime configuration is valid.")


@runtime.command()
@click.argument("targets", nargs=-1, required=True)
@click.option("--saltenv", default="base", show_default=True)
@click.pass_context
def matrix(ctx: click.Context, targets: tuple[str, ...], saltenv: str) -> None:
    """Display runtime fingerprints and packages for TARGETS."""
    try:
        resolver = _resolver(ctx.obj["PROJECT_DIR"])
        active_sets = [resolver.resolve(target, saltenv=saltenv) for target in targets]
    except (ActivationError, OSError, ValueError) as error:
        _fail(error)
    click.echo("TARGET\tFINGERPRINT\tPACKAGES")
    for active_set in active_sets:
        packages = ", ".join(str(package.name) for package in active_set.packages)
        click.echo(f"{active_set.target}\t{active_set.fingerprint[:12]}\t{packages}")


@click.command()
@click.option("--backend", type=click.Choice(["ssh", "minion"]), required=True)
@click.option("--parallel/--no-parallel", default=True, show_default=True)
@click.option("--max-workers", type=click.IntRange(min=1), default=4, show_default=True)
@click.argument("target")
@click.argument("function")
def exec(backend: str, parallel: bool, max_workers: int, target: str, function: str) -> None:
    """Execute a Salt FUNCTION for TARGET through a selected backend."""
    del backend, parallel, max_workers, target, function
    raise click.ClickException("Runtime execution backends are not implemented yet.")


@click.command()
@click.argument("target")
@click.argument("function")
def ssh(target: str, function: str) -> None:
    """Execute a Salt function through the SSH runtime backend (for example state.highstate)."""
    exec.callback("ssh", True, 4, target, function)
