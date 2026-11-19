"""Release and tag related GitHub API operations."""

from __future__ import annotations

from typing import Any

from ab_hub.github.client import GitHubClient


async def list_releases(
    client: GitHubClient,
    owner: str,
    repo: str,
) -> list[dict[str, Any]]:
    return await client.paginate(f"/repos/{owner}/{repo}/releases")


async def list_tags(
    client: GitHubClient,
    owner: str,
    repo: str,
) -> list[dict[str, Any]]:
    return await client.paginate(f"/repos/{owner}/{repo}/tags")
