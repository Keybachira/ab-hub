"""Data access layer for repositories and related entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ab_hub.core.logger import get_logger
from ab_hub.storage.models import (
    ActivitySnapshot,
    Branch,
    Commit,
    Dependency,
    Repository,
    RepositoryTechnology,
    Scan,
    Technology,
)

logger = get_logger(__name__)


def upsert_repository(session: Session, data: dict[str, Any]) -> Repository:
    """Insert or update a repository from GitHub payload."""
    github_id = data["id"]
    stmt = select(Repository).where(Repository.github_id == github_id)
    repo = session.execute(stmt).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    owner_login = data.get("owner", {}).get("login") or data.get("owner", "")

    fields = {
        "name": data["name"],
        "full_name": data["full_name"],
        "owner": owner_login if isinstance(owner_login, str) else str(owner_login),
        "description": data.get("description"),
        "visibility": data.get("visibility") or ("private" if data.get("private") else "public"),
        "default_branch": data.get("default_branch"),
        "html_url": data.get("html_url", ""),
        "clone_url": data.get("clone_url"),
        "is_fork": bool(data.get("fork", False)),
        "is_archived": bool(data.get("archived", False)),
        "is_private": bool(data.get("private", False)),
        "created_at": _parse_dt(data.get("created_at")),
        "updated_at": _parse_dt(data.get("updated_at")),
        "pushed_at": _parse_dt(data.get("pushed_at")),
        "size": int(data.get("size") or 0),
        "last_scanned_at": now,
    }

    if repo is None:
        repo = Repository(github_id=github_id, discovered_at=now, **fields)
        session.add(repo)
        logger.debug("New repository discovered: %s", fields["full_name"])
    else:
        for k, v in fields.items():
            setattr(repo, k, v)

    session.flush()
    return repo


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # GitHub returns ISO 8601 with Z
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def list_repositories(
    session: Session,
    *,
    visibility: str | None = None,
    archived: bool | None = None,
    language: str | None = None,
    owner: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Repository]:
    stmt = select(Repository).order_by(Repository.pushed_at.desc().nullslast())
    if visibility:
        stmt = stmt.where(Repository.visibility == visibility)
    if archived is not None:
        stmt = stmt.where(Repository.is_archived == archived)
    if owner:
        stmt = stmt.where(Repository.owner == owner)
    stmt = stmt.limit(limit).offset(offset)
    return session.execute(stmt).scalars().all()


def get_repository_by_name(session: Session, name: str) -> Repository | None:
    """Find by short name or full_name (case-insensitive-ish)."""
    stmt = select(Repository).where((Repository.name == name) | (Repository.full_name == name))
    return session.execute(stmt).scalar_one_or_none()


def count_repositories(session: Session) -> int:
    from sqlalchemy import func

    return session.execute(select(func.count()).select_from(Repository)).scalar_one()


def create_scan(session: Session) -> Scan:
    scan = Scan(started_at=datetime.now(timezone.utc), status="running")
    session.add(scan)
    session.flush()
    return scan


def finish_scan(
    session: Session,
    scan: Scan,
    *,
    discovered: int,
    analyzed: int,
    errors: list[str] | None = None,
    status: str = "completed",
) -> None:
    import json

    scan.completed_at = datetime.now(timezone.utc)
    scan.status = status
    scan.repositories_discovered = discovered
    scan.repositories_analyzed = analyzed
    if errors:
        scan.errors = json.dumps(errors)
    session.flush()
