"""GitHub API pagination helpers."""

from __future__ import annotations

from typing import Any, AsyncIterator, Callable, Optional
from urllib.parse import parse_qs, urlparse

import httpx


def parse_link_header(link_header: str | None) -> dict[str, str]:
    """Parse GitHub Link header into a dict of rel -> url."""
    links: dict[str, str] = {}
    if not link_header:
        return links
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) < 2:
            continue
        url = section[0].strip()[1:-1]  # remove < >
        for param in section[1:]:
            if "rel=" in param:
                rel = param.split("=")[1].strip().strip('"')
                links[rel] = url
    return links


def has_next_page(response: httpx.Response) -> bool:
    links = parse_link_header(response.headers.get("Link"))
    return "next" in links


def get_next_url(response: httpx.Response) -> Optional[str]:
    links = parse_link_header(response.headers.get("Link"))
    return links.get("next")
