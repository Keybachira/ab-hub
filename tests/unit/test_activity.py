"""Unit tests for activity scoring."""

from datetime import datetime, timedelta, timezone

from ab_hub.analyzers.activity import calculate_activity_score
from ab_hub.core.models import ActivityClassification, CommitInfo


def _commit(days_ago: int) -> CommitInfo:
    return CommitInfo(
        sha="abc",
        message="test",
        author="tester",
        author_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


def test_archived():
    score = calculate_activity_score([], is_archived=True)
    assert score.classification == ActivityClassification.ARCHIVED
    assert score.score == 0.0


def test_active_recent():
    commits = [_commit(i) for i in range(0, 20)]
    score = calculate_activity_score(commits, has_docs=True, has_tests=True)
    assert score.score >= 60
    assert score.classification in (
        ActivityClassification.ACTIVE,
        ActivityClassification.MAINTAINED,
    )


def test_possibly_abandoned():
    commits = [_commit(400)]
    score = calculate_activity_score(commits)
    assert score.classification == ActivityClassification.POSSIBLY_ABANDONED
