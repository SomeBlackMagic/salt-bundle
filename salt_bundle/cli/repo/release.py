"""Release formulas to repository."""

import sys
from pathlib import Path

import click

from salt_bundle import release


@click.command()
@click.option('--formulas-dir', '-f', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              required=True, help='Directory containing formulas (required)')
@click.option('--single', is_flag=True,
              help='Treat formulas-dir as a single formula directory (not subdirectories)')
@click.option('--provider', '-p', type=click.Choice(['local', 'github'], case_sensitive=False),
              required=True, help='Release provider: local (filesystem) or github (GitHub releases)')
@click.option('--pkg-storage-dir', type=click.Path(file_okay=False, dir_okay=True),
              help='[local provider] Directory where packages and index.yaml will be stored (required for local provider)')
@click.option('--index-branch', type=str, default='gh-pages',
              help='[github provider] Git branch for index.yaml (default: gh-pages)')
@click.option('--skip-packaging', is_flag=True,
              help='Skip packaging step (use existing .tgz files)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without doing it')
@click.pass_context
def release(ctx, formulas_dir, single, provider, pkg_storage_dir, index_branch, skip_packaging, dry_run):
    """Release formulas to repository.

    Automates the complete release workflow:
    1. Discovers formulas in the specified directory
    2. Detects new versions (not in repository)
    3. Packages formulas into .tar.gz archives (unless --skip-packaging)
    4. Publishes packages to provider storage
    5. Updates repository index.yaml

    PROVIDERS:

    LOCAL - Filesystem storage
        Stores packages in local directory with structure:
          {pkg-storage-dir}/
            ├── index.yaml
            ├── package-1/
            │   └── package-1-0.1.0.tar.gz
            └── package-2/
                └── package-2-0.1.0.tar.gz

        Required: --pkg-storage-dir

    GITHUB - GitHub Releases
        Creates GitHub releases and stores index.yaml in separate branch:
        - Packages uploaded as release assets
        - index.yaml stored in git branch (default: gh-pages)
        - Branch contains ONLY index.yaml

        Required environment variables:
        - GITHUB_TOKEN: Personal access token with repo permissions
        - GITHUB_REPOSITORY: Repository in format 'owner/repo'

        Optional: --index-branch (default: gh-pages)

    FORMULAS DISCOVERY:

    Default mode (multiple formulas):
        Expects subdirectories, each containing a formula:
          formulas/
            ├── formula-1/
            │   └── .saltbundle.yaml
            └── formula-2/
                └── .saltbundle.yaml

    Single mode (--single):
        Treats formulas-dir as one formula:
          my-formula/
            └── .saltbundle.yaml

    Examples:

        # Local provider
        salt-bundle repo release \\
            --formulas-dir ./formulas \\
            --provider local \\
            --pkg-storage-dir ./repo

        # GitHub provider
        export GITHUB_TOKEN=ghp_xxx
        export GITHUB_REPOSITORY=owner/repo
        salt-bundle repo release \\
            --formulas-dir ./formulas \\
            --provider github

        # Single formula
        salt-bundle repo release \\
            --formulas-dir ./my-formula \\
            --single \\
            --provider local \\
            --pkg-storage-dir ./repo

        # Dry run (preview changes)
        salt-bundle repo release \\
            --formulas-dir ./formulas \\
            --provider local \\
            --pkg-storage-dir ./repo \\
            --dry-run

    Exit codes:
    - 0: Release successful
    - 1: Errors occurred during release

    See also:
    - 'salt-bundle formula pack' to manually package formulas
    - 'salt-bundle repo index' to manually update index
    """
    try:
        formulas_path = Path(formulas_dir)

        if dry_run:
            click.echo("=== DRY RUN MODE ===")

        mode = "single formula" if single else "multiple formulas"
        click.echo(f"Mode: {mode}")
        click.echo(f"Formulas directory: {formulas_path}")
        click.echo(f"Provider: {provider}")

        # Initialize provider
        from salt_bundle.providers import LocalReleaseProvider, GitHubReleaseProvider

        if provider == 'local':
            if not pkg_storage_dir:
                click.echo("Error: --pkg-storage-dir is required for local provider", err=True)
                sys.exit(1)

            storage_path = Path(pkg_storage_dir)
            click.echo(f"Storage directory: {storage_path}")
            click.echo()

            provider_instance = LocalReleaseProvider(storage_path)

        elif provider == 'github':
            import os
            token = os.getenv('GITHUB_TOKEN')
            repo = os.getenv('GITHUB_REPOSITORY')

            if not token or not repo:
                click.echo("Error: GITHUB_TOKEN and GITHUB_REPOSITORY environment variables are required", err=True)
                sys.exit(1)

            click.echo(f"GitHub repository: {repo}")
            click.echo(f"Index branch: {index_branch}")
            click.echo()

            provider_instance = GitHubReleaseProvider(
                token=token,
                repository=repo,
                index_branch=index_branch
            )

        else:
            click.echo(f"Error: Unknown provider: {provider}", err=True)
            sys.exit(1)

        # Run release process
        released, errors = release.release_formulas(
            formulas_path,
            provider_instance,
            skip_packaging=skip_packaging,
            dry_run=dry_run,
            single_formula=single,
        )

        # Summary
        click.echo()
        click.echo("=" * 50)
        click.echo("RELEASE SUMMARY")
        click.echo("=" * 50)

        if released:
            click.echo(f"\n✓ Released {len(released)} package(s):")
            for formula in released:
                click.echo(f"  - {formula.name} {formula.version}")
        else:
            click.echo("\nNo packages released")

        if errors:
            click.echo(f"\n✗ Errors ({len(errors)}):")
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        if dry_run:
            click.echo("\n[DRY RUN] No changes were made")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)
