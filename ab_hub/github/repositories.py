"""Repository related GitHub API operations."""

from __future__ import annotations

from typing import Any

from ab_hub.core.logger import get_logger
from ab_hub.github.client import GitHubClient

logger = get_logger(__name__)


async def list_user_repositories(
    client: GitHubClient,
    *,
    visibility: str = "all",
    affiliation: str = "owner,collaborator,organization_member",
    sort: str = "updated",
    direction: str = "desc",
) -> list[dict[str, Any]]:
    """Discover all repositories accessible by the authenticated user."""
    params = {
        "visibility": visibility,
        "affiliation": affiliation,
        "sort": sort,
        "direction": direction,
    }
    logger.info("Discovering repositories (visibility=%s, affiliation=%s)", visibility, affiliation)
    repos = await client.paginate("/user/repos", params=params)
    logger.info("Discovered %d repositories", len(repos))
    return repos


async def get_repository(client: GitHubClient, owner: str, repo: str) -> dict[str, Any]:
    return await client.get_json(f"/repos/{owner}/{repo}")


async def get_languages(client: GitHubClient, owner: str, repo: str) -> dict[str, int]:
    """Return language -> bytes mapping."""
    data = await client.get_json(f"/repos/{owner}/{repo}/languages")
    return data or {}


async def get_contents(
    client: GitHubClient,
    owner: str,
    repo: str,
    path: str = "",
    ref: str | None = None,
) -> Any:
    params = {}
    if ref:
        params["ref"] = ref
    return await client.get_json(f"/repos/{owner}/{repo}/contents/{path}", params=params or None)
