"""HTTPX-based GitHub REST API client with rate-limit awareness."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

import httpx

from ab_hub.core.config import Settings, get_settings
from ab_hub.core.exceptions import GitHubAPIError, RateLimitError
from ab_hub.core.logger import get_logger
from ab_hub.github.authentication import require_token
from ab_hub.github.pagination import get_next_url, has_next_page

logger = get_logger(__name__)


class GitHubClient:
    """Async GitHub API client."""

    def __init__(self, settings: Settings | None = None, token: str | None = None):
        self.settings = settings or get_settings()
        self.token = token or require_token()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GitHubClient":
        self._client = httpx.AsyncClient(
            base_url=self.settings.github_api_base,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": self.settings.github_api_version,
                "User-Agent": "AB-hub/0.1.0",
            },
            timeout=self.settings.request_timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Client not initialized. Use async with GitHubClient() as client:")
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        retries: int | None = None,
    ) -> httpx.Response:
        retries = retries if retries is not None else self.settings.max_retries
        last_exc: Exception | None = None

        for attempt in range(retries + 1):
            try:
                response = await self.client.request(method, path, params=params)
                self._check_rate_limit(response)

                if response.status_code == 404:
                    raise GitHubAPIError(f"Not found: {path}", status_code=404)
                if response.status_code == 401:
                    raise GitHubAPIError("Unauthorized — check your token", status_code=401)
                if response.status_code == 403:
                    # Could be rate limit or permissions
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    if remaining == "0":
                        reset = response.headers.get("X-RateLimit-Reset")
                        raise RateLimitError(
                            "GitHub rate limit exceeded",
                            reset_at=int(reset) if reset else None,
                        )
                    raise GitHubAPIError(
                        f"Forbidden: {response.text[:200]}",
                        status_code=403,
                        response=response.text,
                    )
                if response.status_code >= 400:
                    raise GitHubAPIError(
                        f"GitHub API error {response.status_code}: {response.text[:300]}",
                        status_code=response.status_code,
                        response=response.text,
                    )
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt < retries:
                    wait = 2**attempt
                    logger.warning("Network error, retrying in %ss: %s", wait, exc)
                    await asyncio.sleep(wait)
                else:
                    raise GitHubAPIError(f"Network failure after retries: {exc}") from exc
            except RateLimitError:
                raise
            except GitHubAPIError:
                raise

        raise GitHubAPIError(f"Request failed after retries: {last_exc}")

    def _check_rate_limit(self, response: httpx.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining is not None and int(remaining) < 10:
            logger.warning("GitHub rate limit low: %s remaining", remaining)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        return await self._request("GET", path, params=params)

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self.get(path, params=params)
        return response.json()

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        per_page: int | None = None,
    ) -> list[Any]:
        """Collect all pages for a list endpoint."""
        params = dict(params or {})
        params["per_page"] = per_page or self.settings.per_page
        results: list[Any] = []
        next_url: str | None = path
        is_first = True

        while next_url:
            if is_first:
                response = await self.get(next_url, params=params)
                is_first = False
            else:
                # next_url is absolute from Link header
                response = await self.client.get(next_url)

            data = response.json()
            if isinstance(data, list):
                results.extend(data)
            else:
                # some endpoints wrap items
                items = data.get("items") or data.get("repositories") or []
                results.extend(items)

            next_url = get_next_url(response)
            if next_url and next_url.startswith(self.settings.github_api_base):
                next_url = next_url[len(self.settings.github_api_base) :]

        return results

    async def get_authenticated_user(self) -> dict[str, Any]:
        return await self.get_json("/user")

    async def get_rate_limit(self) -> dict[str, Any]:
        return await self.get_json("/rate_limit")
