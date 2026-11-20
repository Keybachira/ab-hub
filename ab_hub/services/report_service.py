"""Report generation helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from ab_hub.storage.database import get_session
from ab_hub.storage.models import (
    ActivitySnapshot,
    Repository,
    RepositoryTechnology,
    Technology,
    Vulnerability,
)
from ab_hub.storage.repositories import count_repositories


def generate_summary_report() -> dict[str, Any]:
    with get_session() as session:
        total = count_repositories(session)
        archived = session.execute(
            select(func.count()).select_from(Repository).where(Repository.is_archived.is_(True))
        ).scalar_one()
        private = session.execute(
            select(func.count()).select_from(Repository).where(Repository.is_private.is_(True))
        ).scalar_one()

        classifications: dict[str, int] = {}
        snaps = session.execute(select(ActivitySnapshot)).scalars().all()
        for s in snaps:
            classifications[s.classification] = classifications.get(s.classification, 0) + 1

        tech_counts = session.execute(
            select(Technology.name, func.count(RepositoryTechnology.id))
            .join(RepositoryTechnology)
            .group_by(Technology.name)
            .order_by(func.count(RepositoryTechnology.id).desc())
            .limit(15)
        ).all()

        # Security summary
        total_vulns = session.execute(select(func.count()).select_from(Vulnerability)).scalar_one()
        vuln_by_sev = dict(
            session.execute(
                select(Vulnerability.severity, func.count()).group_by(Vulnerability.severity)
            ).all()
        )
        affected_repos = session.execute(
            select(func.count(func.distinct(Vulnerability.repository_id)))
        ).scalar_one()

        return {
            "total_repositories": total,
            "archived": archived,
            "private": private,
            "public": total - private,
            "classifications": classifications,
            "top_technologies": [{"name": n, "count": c} for n, c in tech_counts],
            "security": {
                "total_vulnerabilities": total_vulns,
                "affected_repositories": affected_repos,
                "by_severity": vuln_by_sev,
            },
        }
