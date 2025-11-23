"""Repository management: index generation and package downloading."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests

from .config import get_cache_dir
from .models.index_models import Index, IndexEntry
from .package import get_package_info
from .utils.hashing import calculate_sha256, verify_digest
from .utils.yaml import dump_yaml, load_yaml


def generate_index(repo_dir: Path | str, base_url: Optional[str] = None) -> Index:
    """Generate or update repository index from .tgz files.

    Args:
        repo_dir: Repository directory containing .tgz files
        base_url: Base URL for package links (e.g., 'https://example.com/repo/')
                  If not provided, uses relative URLs (just filename)

    Returns:
        Index object with all packages

    Raises:
        ValueError: If no .tgz files found
    """
    repo_dir = Path(repo_dir)
    if not repo_dir.exists():
        raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

    # Load existing index if present
    index_file = repo_dir / 'index.yaml'
    if index_file.exists():
        data = load_yaml(index_file)
        index = Index(**data)
    else:
        index = Index(generated=datetime.now(), packages={})

    # Find all .tgz files
    tgz_files = list(repo_dir.glob('*.tgz'))
    if not tgz_files:
        raise ValueError(f"No .tgz files found in {repo_dir}")

    # Process each archive
    for archive_path in tgz_files:
        try:
            # Extract metadata
            meta = get_package_info(archive_path)
            digest = calculate_sha256(archive_path)

            # Generate URL
            if base_url:
                # Ensure base_url ends with /
                base = base_url if base_url.endswith('/') else base_url + '/'
                url = urljoin(base, archive_path.name)
            else:
                # Relative URL
                url = archive_path.name

            # Create index entry with metadata
            entry = IndexEntry(
                version=meta.version,
                url=url,
                digest=digest,
                created=datetime.now(),
                keywords=meta.keywords,
                maintainers=meta.maintainers,
                sources=meta.sources
            )

            # Add to index
            if meta.name not in index.packages:
                index.packages[meta.name] = []

            # Check if version already exists
            existing_versions = [e.version for e in index.packages[meta.name]]
            if meta.version not in existing_versions:
                index.packages[meta.name].append(entry)

        except Exception as e:
            print(f"Warning: Failed to process {archive_path}: {e}")
            continue

    # Sort versions (latest first)
    for name in index.packages:
        index.packages[name].sort(key=lambda e: e.version, reverse=True)

    # Update generation timestamp
    index.generated = datetime.now()

    return index


def save_index(index: Index, repo_dir: Path | str) -> None:
    """Save index to index.yaml file.

    Args:
        index: Index object
        repo_dir: Repository directory
    """
    repo_dir = Path(repo_dir)
    index_file = repo_dir / 'index.yaml'
    dump_yaml(index.model_dump(), index_file)


def fetch_index(repo_url: str) -> Index:
    """Fetch repository index from URL.

    Args:
        repo_url: Repository base URL (HTTP or file://)

    Returns:
        Index object

    Raises:
        ValueError: If URL scheme is not supported
        requests.RequestException: If HTTP request fails
        FileNotFoundError: If file:// path doesn't exist
    """
    parsed = urlparse(repo_url)

    if parsed.scheme in ('http', 'https'):
        # HTTP repository
        index_url = urljoin(repo_url, 'index.yaml')
        response = requests.get(index_url, timeout=30)
        response.raise_for_status()
        
        import yaml
        data = yaml.safe_load(response.text)
        return Index(**data)

    elif parsed.scheme == 'file' or not parsed.scheme:
        # File repository
        if parsed.scheme == 'file':
            repo_path = Path(parsed.path)
        else:
            repo_path = Path(repo_url)

        index_file = repo_path / 'index.yaml'
        if not index_file.exists():
            raise FileNotFoundError(f"Index not found: {index_file}")

        data = load_yaml(index_file)
        return Index(**data)

    else:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")


def download_package(
    url: str,
    repo_url: str,
    expected_digest: str,
    cache_dir: Optional[Path] = None
) -> Path:
    """Download package from repository with caching.

    Args:
        url: Package URL (can be relative)
        repo_url: Repository base URL
        expected_digest: Expected SHA256 digest
        cache_dir: Cache directory (defaults to ~/.cache/salt-bundle/packages)

    Returns:
        Path to downloaded package in cache

    Raises:
        ValueError: If digest doesn't match
        requests.RequestException: If download fails
    """
    if cache_dir is None:
        cache_dir = get_cache_dir() / 'packages'
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Determine cache filename from digest
    digest_hash = expected_digest.split(':')[1]
    cache_file = cache_dir / f"{digest_hash}.tgz"

    # Check if already cached
    if cache_file.exists():
        if verify_digest(cache_file, expected_digest):
            return cache_file
        else:
            # Corrupted cache, remove
            cache_file.unlink()

    # Download package
    parsed = urlparse(url)
    
    if parsed.scheme in ('http', 'https'):
        # Absolute URL
        download_url = url
    else:
        # Relative URL, join with repo base
        download_url = urljoin(repo_url, url)

    parsed_download = urlparse(download_url)

    if parsed_download.scheme in ('http', 'https'):
        # HTTP download
        response = requests.get(download_url, timeout=60, stream=True)
        response.raise_for_status()

        with open(cache_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    elif parsed_download.scheme == 'file' or not parsed_download.scheme:
        # File copy
        if parsed_download.scheme == 'file':
            source_path = Path(parsed_download.path)
        else:
            # Relative path from repo
            parsed_repo = urlparse(repo_url)
            if parsed_repo.scheme == 'file':
                repo_path = Path(parsed_repo.path)
            else:
                repo_path = Path(repo_url)
            source_path = repo_path / url

        if not source_path.exists():
            raise FileNotFoundError(f"Package not found: {source_path}")

        shutil.copy2(source_path, cache_file)

    else:
        raise ValueError(f"Unsupported URL scheme: {parsed_download.scheme}")

    # Verify digest
    if not verify_digest(cache_file, expected_digest):
        cache_file.unlink()
        raise ValueError(f"Digest mismatch for {url}")

    return cache_file
