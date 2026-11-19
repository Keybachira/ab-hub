"""Commit analysis helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ab_hub.core.models import CommitInfo


def parse_commit(raw: dict[str, Any]) -> CommitInfo:
    commit = raw.get("commit") or {}
    author = commit.get("author") or {}
    committer = commit.get("committer") or {}
    return CommitInfo(
        sha=raw.get("sha", ""),
        message=(commit.get("message") or "")[:2000],
        author=author.get("name") or (raw.get("author") or {}).get("login"),
        author_date=_parse_dt(author.get("date")),
        committer_date=_parse_dt(committer.get("date")),
    )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def compute_commit_stats(commits: list[CommitInfo]) -> dict[str, Any]:
    """Basic temporal statistics."""
    if not commits:
        return {
            "total": 0,
            "commits_7d": 0,
            "commits_30d": 0,
            "commits_90d": 0,
            "last_commit_at": None,
            "avg_days_between": None,
        }

    now = datetime.now(timezone.utc)
    dates = sorted(
        [c.author_date for c in commits if c.author_date],
        reverse=True,
    )
    if not dates:
        return {
            "total": len(commits),
            "commits_7d": 0,
            "commits_30d": 0,
            "commits_90d": 0,
            "last_commit_at": None,
            "avg_days_between": None,
        }

    def count_since(days: int) -> int:
        threshold = now.timestamp() - days * 86400
        return sum(1 for d in dates if d.timestamp() >= threshold)

    gaps = []
    for i in range(len(dates) - 1):
        delta = (dates[i] - dates[i + 1]).total_seconds() / 86400
        gaps.append(delta)

    avg_gap = sum(gaps) / len(gaps) if gaps else None

    return {
        "total": len(commits),
        "commits_7d": count_since(7),
        "commits_30d": count_since(30),
        "commits_90d": count_since(90),
        "last_commit_at": dates[0],
        "avg_days_between": round(avg_gap, 1) if avg_gap is not None else None,
    }
