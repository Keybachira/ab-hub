"""Project classification facade."""

from __future__ import annotations

from ab_hub.analyzers.activity import calculate_activity_score
from ab_hub.core.models import ActivityScore, CommitInfo


def classify_repository(
    commits: list[CommitInfo],
    *,
    is_archived: bool = False,
    has_docs: bool = False,
    has_tests: bool = False,
) -> ActivityScore:
    """Public entry point for activity classification."""
    return calculate_activity_score(
        commits,
        is_archived=is_archived,
        has_docs=has_docs,
        has_tests=has_tests,
    )
