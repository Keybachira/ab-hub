"""Repository inspection helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import selectinload

from ab_hub.storage.database import get_session
from ab_hub.storage.models import Repository
from ab_hub.storage.repositories import get_repository_by_name


def inspect_repository(name: str) -> dict[str, Any] | None:
    with get_session() as session:
        repo = get_repository_by_name(session, name)
        if repo is None:
            return None

        # load relationships
        session.refresh(repo)
        techs = [
            {
                "name": rt.technology.name,
                "category": rt.technology.category,
                "confidence": rt.confidence,
                "method": rt.detection_method,
                "evidence": rt.evidence,
            }
            for rt in repo.technologies
        ]
        latest_activity = None
        if repo.activity_snapshots:
            snap = sorted(repo.activity_snapshots, key=lambda s: s.snapshot_date, reverse=True)[0]
            latest_activity = {
                "score": snap.activity_score,
                "classification": snap.classification,
                "date": snap.snapshot_date.isoformat() if snap.snapshot_date else None,
            }

        return {
            "id": repo.id,
            "github_id": repo.github_id,
            "name": repo.name,
            "full_name": repo.full_name,
            "owner": repo.owner,
            "description": repo.description,
            "visibility": repo.visibility,
            "is_private": repo.is_private,
            "is_fork": repo.is_fork,
            "is_archived": repo.is_archived,
            "default_branch": repo.default_branch,
            "html_url": repo.html_url,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "size": repo.size,
            "last_scanned_at": repo.last_scanned_at.isoformat() if repo.last_scanned_at else None,
            "technologies": techs,
            "commit_count": len(repo.commits),
            "branch_count": len(repo.branches),
            "activity": latest_activity,
        }
