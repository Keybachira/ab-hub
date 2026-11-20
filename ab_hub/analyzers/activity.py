"""Activity scoring algorithm."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ab_hub.core.models import ActivityClassification, ActivityScore
from ab_hub.analyzers.commits import compute_commit_stats
from ab_hub.core.models import CommitInfo


def calculate_activity_score(
    commits: list[CommitInfo],
    *,
    is_archived: bool = False,
    has_docs: bool = False,
    has_tests: bool = False,
) -> ActivityScore:
    """
    Compute activity score 0–100 and classification.

    Weights (v0.1):
      - Recency          35
      - Frequency        25
      - Recent evolution 20
      - Maintenance      10
      - Docs & tests     10
    """
    if is_archived:
        return ActivityScore(
            score=0.0,
            classification=ActivityClassification.ARCHIVED,
            evidence={"reason": "O repositório está arquivado"},
        )

    stats = compute_commit_stats(commits)
    evidence: dict[str, Any] = dict(stats)

    # Recency (0–35)
    last = stats.get("last_commit_at")
    recency = 0.0
    if last:
        days_ago = (datetime.now(timezone.utc) - last).total_seconds() / 86400
        if days_ago <= 7:
            recency = 35.0
        elif days_ago <= 30:
            recency = 28.0
        elif days_ago <= 90:
            recency = 18.0
        elif days_ago <= 180:
            recency = 10.0
        elif days_ago <= 365:
            recency = 5.0
        else:
            recency = 0.0
        evidence["days_since_last_commit"] = round(days_ago, 1)

    # Frequency (0–25) based on 90-day volume
    c90 = stats.get("commits_90d", 0)
    if c90 >= 30:
        frequency = 25.0
    elif c90 >= 15:
        frequency = 20.0
    elif c90 >= 5:
        frequency = 12.0
    elif c90 >= 1:
        frequency = 6.0
    else:
        frequency = 0.0

    # Recent evolution (0–20) – commits in last 30 days relative to 90
    c30 = stats.get("commits_30d", 0)
    if c90 > 0:
        ratio = c30 / c90
        evolution = min(20.0, ratio * 25)
    else:
        evolution = 0.0

    # Maintenance heuristic (0–10) – presence of recent activity + not too sparse
    maintenance = 5.0 if c30 > 0 else 0.0
    if stats.get("avg_days_between") and stats["avg_days_between"] < 14:
        maintenance += 5.0
    maintenance = min(10.0, maintenance)

    # Docs & tests (0–10)
    docs_tests = 0.0
    if has_docs:
        docs_tests += 5.0
    if has_tests:
        docs_tests += 5.0

    score = recency + frequency + evolution + maintenance + docs_tests
    score = max(0.0, min(100.0, round(score, 1)))

    if score >= 80:
        classification = ActivityClassification.ACTIVE
    elif score >= 60:
        classification = ActivityClassification.MAINTAINED
    elif score >= 35:
        classification = ActivityClassification.DORMANT
    else:
        classification = ActivityClassification.POSSIBLY_ABANDONED

    evidence.update(
        {
            "recency_points": recency,
            "frequency_points": frequency,
            "evolution_points": round(evolution, 1),
            "maintenance_points": maintenance,
            "docs_tests_points": docs_tests,
        }
    )

    return ActivityScore(
        score=score,
        classification=classification,
        evidence=evidence,
        commits_7d=stats.get("commits_7d", 0),
        commits_30d=stats.get("commits_30d", 0),
        commits_90d=stats.get("commits_90d", 0),
        last_commit_at=stats.get("last_commit_at"),
        avg_days_between_commits=stats.get("avg_days_between"),
    )
