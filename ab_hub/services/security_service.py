"""Security monitoring service."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from ab_hub.analyzers.dependencies import extract_dependencies_from_files
from ab_hub.analyzers.security import SEVERITY_ORDER, scan_dependencies_for_vulns, security_score
from ab_hub.core.logger import get_logger
from ab_hub.core.models import DependencyInfo
from ab_hub.github.client import GitHubClient
from ab_hub.github.repositories import get_contents
from ab_hub.storage.database import get_session, init_db
from ab_hub.storage.models import Dependency, Repository, Vulnerability
from ab_hub.storage.repositories import get_repository_by_name

logger = get_logger(__name__)

# Manifest files we will try to fetch from the repository root
MANIFEST_CANDIDATES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    "composer.json",
]


async def fetch_manifest_contents(
    client: GitHubClient,
    owner: str,
    repo: str,
) -> dict[str, str]:
    """Download known manifest files from the repository root (best-effort)."""
    files: dict[str, str] = {}
    for name in MANIFEST_CANDIDATES:
        try:
            data = await get_contents(client, owner, repo, path=name)
            if isinstance(data, dict) and data.get("encoding") == "base64" and data.get("content"):
                content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                files[name] = content
            elif isinstance(data, dict) and data.get("type") == "file" and "download_url" in data:
                # Fallback via raw download not implemented here; base64 is preferred
                pass
        except Exception as exc:  # noqa: BLE001
            logger.debug("Manifest %s not available for %s/%s: %s", name, owner, repo, exc)
    return files


async def analyze_repository_security(
    client: GitHubClient,
    repo: Repository,
    *,
    session,
) -> dict[str, Any]:
    """
    Full security pass for one repository:
    1. Fetch manifests
    2. Parse dependencies
    3. Query OSV
    4. Persist Dependency + Vulnerability rows
    """
    files = await fetch_manifest_contents(client, repo.owner, repo.name)
    deps_info = extract_dependencies_from_files(files)

    # Persist dependencies (replace previous set)
    session.query(Dependency).filter_by(repository_id=repo.id).delete()
    for d in deps_info:
        session.add(
            Dependency(
                repository_id=repo.id,
                name=d.name,
                version=d.version,
                ecosystem=d.ecosystem,
                manifest_file=d.manifest_file,
            )
        )

    findings = await scan_dependencies_for_vulns(deps_info)

    # Replace previous vulnerability findings for this repo
    session.query(Vulnerability).filter_by(repository_id=repo.id).delete()
    now = datetime.now(timezone.utc)
    for f in findings:
        session.add(
            Vulnerability(
                repository_id=repo.id,
                osv_id=f.get("osv_id"),
                ghsa_id=f.get("ghsa_id"),
                cve_id=f.get("cve_id"),
                package_name=f["package_name"],
                ecosystem=f["ecosystem"],
                installed_version=f.get("installed_version"),
                severity=f.get("severity") or "UNKNOWN",
                summary=f.get("summary"),
                details=f.get("details"),
                fixed_version=f.get("fixed_version"),
                published_at=f.get("published_at"),
                modified_at=f.get("modified_at"),
                source=f.get("source") or "osv",
                is_direct=f.get("is_direct", True),
                cvss_score=f.get("cvss_score"),
                detected_at=now,
                dismissed=False,
            )
        )

    session.flush()
    summary = security_score(findings)
    return {
        "repository": repo.full_name,
        "dependencies": len(deps_info),
        "vulnerabilities": len(findings),
        "summary": summary,
        "findings": findings,
    }


async def run_security_scan(
    *,
    repo_name: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Run security analysis on one repository or on a batch of recently scanned ones.
    """
    init_db()
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    with get_session() as session:
        if repo_name:
            repos = []
            r = get_repository_by_name(session, repo_name)
            if r:
                repos = [r]
            else:
                return {"error": f"Repository not found: {repo_name}"}
        else:
            stmt = (
                select(Repository)
                .where(Repository.is_archived.is_(False))
                .order_by(Repository.last_scanned_at.desc().nullslast())
                .limit(limit)
            )
            repos = list(session.execute(stmt).scalars())

        if not repos:
            return {"processed": 0, "results": [], "errors": ["No repositories to scan"]}

        async with GitHubClient() as client:
            for repo in repos:
                try:
                    result = await analyze_repository_security(client, repo, session=session)
                    results.append(result)
                    session.commit()
                except Exception as exc:  # noqa: BLE001
                    session.rollback()
                    msg = f"{repo.full_name}: {exc}"
                    errors.append(msg)
                    logger.warning(msg)

    total_vulns = sum(r.get("vulnerabilities", 0) for r in results)
    return {
        "processed": len(results),
        "total_vulnerabilities": total_vulns,
        "results": results,
        "errors": errors,
    }


def get_security_overview() -> dict[str, Any]:
    """Aggregate security posture across the local database."""
    init_db()
    with get_session() as session:
        total_vulns = session.execute(select(func.count()).select_from(Vulnerability)).scalar_one()
        by_severity = dict(
            session.execute(
                select(Vulnerability.severity, func.count()).group_by(Vulnerability.severity)
            ).all()
        )
        top_packages = session.execute(
            select(Vulnerability.package_name, func.count())
            .group_by(Vulnerability.package_name)
            .order_by(func.count().desc())
            .limit(15)
        ).all()
        affected_repos = session.execute(
            select(func.count(func.distinct(Vulnerability.repository_id)))
        ).scalar_one()

        # Most critical findings
        critical = (
            session.execute(
                select(Vulnerability)
                .where(Vulnerability.severity.in_(["CRITICAL", "HIGH"]))
                .order_by(Vulnerability.detected_at.desc())
                .limit(20)
            )
            .scalars()
            .all()
        )

        return {
            "total_vulnerabilities": total_vulns,
            "affected_repositories": affected_repos,
            "by_severity": by_severity,
            "top_vulnerable_packages": [{"name": n, "count": c} for n, c in top_packages],
            "recent_critical_or_high": [
                {
                    "package": v.package_name,
                    "severity": v.severity,
                    "osv_id": v.osv_id,
                    "cve_id": v.cve_id,
                    "installed": v.installed_version,
                    "fixed": v.fixed_version,
                    "repository_id": v.repository_id,
                }
                for v in critical
            ],
        }


def list_vulnerabilities_for_repo(name: str) -> list[dict[str, Any]] | None:
    init_db()
    with get_session() as session:
        repo = get_repository_by_name(session, name)
        if repo is None:
            return None
        vulns = (
            session.execute(
                select(Vulnerability)
                .where(Vulnerability.repository_id == repo.id)
                .order_by(Vulnerability.severity.desc())
            )
            .scalars()
            .all()
        )
        # Sort by severity weight
        vulns = sorted(
            vulns,
            key=lambda v: SEVERITY_ORDER.get((v.severity or "").upper(), 0),
            reverse=True,
        )
        return [
            {
                "package": v.package_name,
                "ecosystem": v.ecosystem,
                "installed_version": v.installed_version,
                "severity": v.severity,
                "osv_id": v.osv_id,
                "ghsa_id": v.ghsa_id,
                "cve_id": v.cve_id,
                "summary": v.summary,
                "fixed_version": v.fixed_version,
                "cvss_score": v.cvss_score,
                "source": v.source,
                "detected_at": v.detected_at.isoformat() if v.detected_at else None,
            }
            for v in vulns
        ]
