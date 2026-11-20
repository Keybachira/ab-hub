"""Commit related GitHub API operations."""

from __future__ import annotations

from typing import Any

from ab_hub.core.logger import get_logger
from ab_hub.github.client import GitHubClient

logger = get_logger(__name__)


async def list_commits(
    client: GitHubClient,
    owner: str,
    repo: str,
    *,
    sha: str | None = None,
    per_page: int = 30,
    max_pages: int = 3,
) -> list[dict[str, Any]]:
    """
    List recent commits.
    By default only a limited number of pages are fetched
    to keep scanning fast and respectful of rate limits.
    """
    params: dict[str, Any] = {"per_page": per_page}
    if sha:
        params["sha"] = sha

    results: list[dict[str, Any]] = []
    path = f"/repos/{owner}/{repo}/commits"
    next_url: str | None = path
    pages = 0

    while next_url and pages < max_pages:
        if pages == 0:
            response = await client.get(next_url, params=params)
        else:
            response = await client.client.get(next_url)

        data = response.json()
        if isinstance(data, list):
            results.extend(data)
        pages += 1

        from ab_hub.github.pagination import get_next_url

        next_url = get_next_url(response)
        if next_url and next_url.startswith(client.settings.github_api_base):
            next_url = next_url[len(client.settings.github_api_base) :]

    logger.debug("Fetched %d commits for %s/%s", len(results), owner, repo)
    return results
