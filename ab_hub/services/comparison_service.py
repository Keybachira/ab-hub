"""Simple repository comparison."""

from __future__ import annotations

from typing import Any

from ab_hub.services.inspection_service import inspect_repository


def compare_repositories(name_a: str, name_b: str) -> dict[str, Any] | None:
    a = inspect_repository(name_a)
    b = inspect_repository(name_b)
    if a is None or b is None:
        return None
    return {
        "a": a,
        "b": b,
        "diff": {
            "activity_score": {
                "a": (a.get("activity") or {}).get("score"),
                "b": (b.get("activity") or {}).get("score"),
            },
            "technologies_a_only": sorted(
                set(t["name"] for t in a.get("technologies", []))
                - set(t["name"] for t in b.get("technologies", []))
            ),
            "technologies_b_only": sorted(
                set(t["name"] for t in b.get("technologies", []))
                - set(t["name"] for t in a.get("technologies", []))
            ),
            "common_technologies": sorted(
                set(t["name"] for t in a.get("technologies", []))
                & set(t["name"] for t in b.get("technologies", []))
            ),
        },
    }
