"""High-level discovery scanner."""

from __future__ import annotations

from ab_hub.core.logger import get_logger
from ab_hub.discovery.repository_discovery import discover_all_repositories
from ab_hub.github.client import GitHubClient

logger = get_logger(__name__)


async def run_discovery(client: GitHubClient) -> list[dict]:
    """Entry point for repository discovery."""
    return await discover_all_repositories(client)
