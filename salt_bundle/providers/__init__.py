"""Release providers for salt-bundle."""

from .base import ReleaseProvider
from .github_provider import GitHubReleaseProvider
from .local_provider import LocalReleaseProvider

__all__ = ['ReleaseProvider', 'LocalReleaseProvider', 'GitHubReleaseProvider']
