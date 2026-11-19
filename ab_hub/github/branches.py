"""Branch related GitHub API operations."""

from __future__ import annotations

from typing import Any

from ab_hub.github.client import GitHubClient


async def list_branches(
    client: GitHubClient,
    owner: str,
    repo: str,
    *,
    protected: bool | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if protected is not None:
        params["protected"] = str(protected).lower()
    return await client.paginate(f"/repos/{owner}/{repo}/branches", params=params or None)
