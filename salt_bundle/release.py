"""Release automation: detect, pack and publish formulas."""

from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from .config import load_package_meta
from .models.index_models import Index, IndexEntry
from .models.package_models import PackageMeta
from .package import pack_formula, validate_package_name, validate_semver
from .providers.base import ReleaseProvider
from .utils.hashing import calculate_sha256


class FormulaInfo:
    """Information about a formula to be released."""

    def __init__(self, path: Path, meta: PackageMeta):
        """Initialize formula info.

        Args:
            path: Path to formula directory
            meta: Package metadata
        """
        self.path = path
        self.meta = meta
        self.name = meta.name
        self.version = meta.version


def discover_formulas(formulas_dir: Path | str, single_formula: bool = False) -> List[FormulaInfo]:
    """Discover all formulas in a directory.

    Args:
        formulas_dir: Directory containing formula subdirectories or single formula
        single_formula: If True, treat formulas_dir as a single formula directory

    Returns:
        List of FormulaInfo objects

    Raises:
        FileNotFoundError: If formulas_dir doesn't exist
    """
    formulas_dir = Path(formulas_dir)

    if not formulas_dir.exists():
        raise FileNotFoundError(f"Formulas directory not found: {formulas_dir}")

    formulas = []

    # Check if this is a single formula directory
    if single_formula or (formulas_dir / '.saltbundle.yaml').exists():
        # Treat as single formula
        try:
            # Load metadata
            meta = load_package_meta(formulas_dir)

            # Validate
            if not validate_package_name(meta.name):
                print(f"Warning: Invalid package name in {formulas_dir}: {meta.name}")
                return formulas

            if not validate_semver(meta.version):
                print(f"Warning: Invalid semver in {formulas_dir}: {meta.version}")
                return formulas

            # Check for at least one .sls file
            sls_files = list(formulas_dir.glob('*.sls'))
            if not sls_files:
                print(f"Warning: No .sls files found in {formulas_dir}")
                return formulas

            formulas.append(FormulaInfo(formulas_dir, meta))

        except Exception as e:
            print(f"Warning: Failed to load formula from {formulas_dir}: {e}")

        return formulas

    # Otherwise, iterate through subdirectories
    for item in formulas_dir.iterdir():
        if not item.is_dir():
            continue

        # Check for .saltbundle.yaml
        saltbundle_yaml = item / '.saltbundle.yaml'
        if not saltbundle_yaml.exists():
            continue

        try:
            # Load metadata
            meta = load_package_meta(item)

            # Validate
            if not validate_package_name(meta.name):
                print(f"Warning: Invalid package name in {item}: {meta.name}")
                continue

            if not validate_semver(meta.version):
                print(f"Warning: Invalid semver in {item}: {meta.version}")
                continue

            # Check for at least one .sls file
            sls_files = list(item.glob('*.sls'))
            if not sls_files:
                print(f"Warning: No .sls files found in {item}")
                continue

            formulas.append(FormulaInfo(item, meta))

        except Exception as e:
            print(f"Warning: Failed to load formula from {item}: {e}")
            continue

    return formulas


def is_new_version(formula: FormulaInfo, index: Index | None) -> bool:
    """Check if formula version is new (not in index).

    Args:
        formula: Formula information
        index: Repository index (None if empty)

    Returns:
        True if version is new, False otherwise
    """
    if index is None:
        return True

    if formula.name not in index.packages:
        return True

    existing_versions = [entry.version for entry in index.packages[formula.name]]
    return formula.version not in existing_versions


def release_formulas(
    formulas_dir: Path | str,
    provider: ReleaseProvider,
    skip_packaging: bool = False,
    dry_run: bool = False,
    single_formula: bool = False,
) -> Tuple[List[FormulaInfo], List[str]]:
    """Release formulas using the specified provider.

    Args:
        formulas_dir: Directory containing formula subdirectories or single formula
        provider: Release provider (LocalReleaseProvider or GitHubReleaseProvider)
        skip_packaging: Skip packaging step (use existing .tgz files)
        dry_run: Show what would be done without actually doing it
        single_formula: If True, treat formulas_dir as a single formula directory

    Returns:
        Tuple of (released_formulas, errors)

    Raises:
        FileNotFoundError: If directories don't exist
    """
    formulas_dir = Path(formulas_dir)

    if not formulas_dir.exists():
        raise FileNotFoundError(f"Formulas directory not found: {formulas_dir}")

    # Initialize provider
    if not dry_run:
        try:
            provider.initialize()
        except Exception as e:
            return [], [f"Failed to initialize provider: {e}"]

    # Load existing index
    index = None
    if not dry_run:
        try:
            index = provider.load_index()
            if index:
                total_versions = sum(len(versions) for versions in index.packages.values())
                print(f"Loaded existing index with {len(index.packages)} packages, {total_versions} total versions")
                for pkg_name, versions in index.packages.items():
                    print(f"  - {pkg_name}: {len(versions)} version(s)")
            else:
                print("No existing index found, will create new one")
        except Exception as e:
            print(f"Warning: Failed to load index: {e}")

    # Discover formulas
    formulas = discover_formulas(formulas_dir, single_formula=single_formula)
    if not formulas:
        return [], ["No valid formulas found"]

    released = []
    errors = []

    # Create temporary directory for packaging
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix='salt-pkg-'))

    try:
        # Process each formula
        for formula in formulas:
            # Check if version is new
            if not is_new_version(formula, index):
                print(f"Skipping {formula.name} {formula.version} (already released)")
                continue

            print(f"Processing {formula.name} {formula.version}...")

            if dry_run:
                print(f"  [DRY RUN] Would release {formula.name} {formula.version}")
                released.append(formula)
                continue

            try:
                # Pack formula to temp directory
                if not skip_packaging:
                    archive_path = pack_formula(formula.path, temp_dir)
                    print(f"  Packed: {archive_path.name}")
                else:
                    # Look for existing archive in temp or formula dir
                    archive_name = f"{formula.name}-{formula.version}.tgz"
                    archive_path = temp_dir / archive_name
                    if not archive_path.exists():
                        archive_path = formula.path / archive_name
                    if not archive_path.exists():
                        errors.append(f"{formula.name}: Archive not found: {archive_name}")
                        continue
                    print(f"  Using existing: {archive_path.name}")

                # Upload package via provider
                url = provider.upload_package(formula.name, formula.version, archive_path)
                print(f"  Uploaded: {url}")

                # Add to released list with URL info
                formula.release_url = url
                released.append(formula)

            except Exception as e:
                error_msg = f"{formula.name}: {e}"
                errors.append(error_msg)
                print(f"  Error: {e}")
                continue

        # Update index if we released something
        if released and not dry_run:
            try:
                print("\nUpdating package index...")

                # Start with existing index or create new one
                if index is None:
                    index = Index(generated=datetime.now(), packages={})

                # Add new releases to index
                for formula in released:
                    archive_name = f"{formula.name}-{formula.version}.tgz"
                    archive_path = temp_dir / archive_name

                    if archive_path.exists():
                        digest = calculate_sha256(archive_path)

                        # Create index entry with metadata from formula
                        entry = IndexEntry(
                            version=formula.version,
                            url=getattr(formula, 'release_url', archive_name),
                            digest=digest,
                            created=datetime.now(),
                            keywords=formula.meta.keywords,
                            maintainers=formula.meta.maintainers,
                            sources=formula.meta.sources
                        )

                        # Add to index
                        if formula.name not in index.packages:
                            index.packages[formula.name] = []

                        # Check if version already exists (shouldn't happen, but double-check)
                        existing_versions = [e.version for e in index.packages[formula.name]]
                        if formula.version not in existing_versions:
                            index.packages[formula.name].append(entry)
                            print(f"  Added {formula.name} {formula.version} to index")
                        else:
                            print(f"  Warning: {formula.name} {formula.version} already exists in index, skipping")

                # Sort versions (latest first)
                for name in index.packages:
                    index.packages[name].sort(key=lambda e: e.version, reverse=True)

                # Update generation timestamp
                index.generated = datetime.now()

                # Save index via provider
                provider.save_index(index)
                print(f"Index updated: {len(index.packages)} packages total")

            except Exception as e:
                errors.append(f"Failed to update index: {e}")

    finally:
        # Clean up temp directory
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    return released, errors
