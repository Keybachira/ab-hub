"""Organization discovery helpers (placeholder for future expansion)."""

from __future__ import annotations

from typing import Any

from ab_hub.github.client import GitHubClient


async def list_user_organizations(client: GitHubClient) -> list[dict[str, Any]]:
    """Return organizations the authenticated user belongs to."""
    return await client.paginate("/user/orgs")
