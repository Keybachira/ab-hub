"""Repository discovery logic."""

from __future__ import annotations

from typing import Any

from ab_hub.core.logger import get_logger
from ab_hub.github.client import GitHubClient
from ab_hub.github.repositories import list_user_repositories

logger = get_logger(__name__)


async def discover_all_repositories(client: GitHubClient) -> list[dict[str, Any]]:
    """
    Discover every repository the authenticated user can access.
    Deduplicates by GitHub ID.
    """
    raw = await list_user_repositories(
        client,
        visibility="all",
        affiliation="owner,collaborator,organization_member",
    )
    seen: set[int] = set()
    unique: list[dict[str, Any]] = []
    for repo in raw:
        rid = repo.get("id")
        if rid is None or rid in seen:
            continue
        seen.add(rid)
        unique.append(repo)
    logger.info("Unique repositories after deduplication: %d", len(unique))
    return unique
