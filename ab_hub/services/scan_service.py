"""Scan orchestration service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from ab_hub.analyzers.activity import calculate_activity_score
from ab_hub.analyzers.commits import parse_commit
from ab_hub.analyzers.structure import extract_paths_from_contents, has_documentation, has_tests
from ab_hub.analyzers.technology import (
    detect_from_file_tree,
    detect_from_languages,
    merge_technologies,
)
from ab_hub.core.logger import get_logger
from ab_hub.discovery.scanner import run_discovery
from ab_hub.github.client import GitHubClient
from ab_hub.github.commits import list_commits
from ab_hub.github.repositories import get_contents, get_languages
from ab_hub.storage.database import get_session, init_db
from ab_hub.storage.models import ActivitySnapshot, Commit, RepositoryTechnology, Technology
from ab_hub.storage.repositories import create_scan, finish_scan, upsert_repository

logger = get_logger(__name__)
console = Console()


async def run_full_scan(*, incremental: bool = False, run_security: bool = False) -> dict[str, Any]:
    """
    Main scan entry point.
    Discovers repositories, persists them, collects basic intelligence.
    """
    init_db()
    errors: list[str] = []
    discovered = 0
    analyzed = 0

    with get_session() as session:
        scan = create_scan(session)
        session.commit()  # ensure scan id exists

        async with GitHubClient() as client:
            # Authenticated user check
            user = await client.get_authenticated_user()
            console.print(f"[bold green]Authenticated as[/] {user.get('login')}")

            repos = await run_discovery(client)
            discovered = len(repos)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Analyzing repositories…", total=len(repos))

                for raw in repos:
                    full_name = raw.get("full_name", "?")
                    try:
                        repo = upsert_repository(session, raw)
                        owner = repo.owner
                        name = repo.name

                        # Languages
                        try:
                            languages = await get_languages(client, owner, name)
                            tech_from_lang = detect_from_languages(languages)
                        except Exception as exc:  # noqa: BLE001
                            logger.debug("Languages failed for %s: %s", full_name, exc)
                            tech_from_lang = []

                        # Root contents (for signatures)
                        paths: list[str] = []
                        try:
                            contents = await get_contents(client, owner, name)
                            paths = extract_paths_from_contents(contents)
                        except Exception as exc:  # noqa: BLE001
                            logger.debug("Contents failed for %s: %s", full_name, exc)

                        tech_from_files = detect_from_file_tree(paths)
                        technologies = merge_technologies(tech_from_lang, tech_from_files)

                        # Persist technologies
                        for tinfo in technologies:
                            tech = (
                                session.query(Technology).filter_by(name=tinfo.name).one_or_none()
                            )
                            if tech is None:
                                tech = Technology(name=tinfo.name, category=tinfo.category.value)
                                session.add(tech)
                                session.flush()
                            link = (
                                session.query(RepositoryTechnology)
                                .filter_by(repository_id=repo.id, technology_id=tech.id)
                                .one_or_none()
                            )
                            if link is None:
                                link = RepositoryTechnology(
                                    repository_id=repo.id,
                                    technology_id=tech.id,
                                    confidence=tinfo.confidence,
                                    evidence=tinfo.evidence,
                                    detection_method=tinfo.detection_method.value,
                                    detected_at=datetime.now(timezone.utc),
                                )
                                session.add(link)

                        # Commits (limited)
                        try:
                            raw_commits = await list_commits(client, owner, name, max_pages=2)
                            commit_infos = [parse_commit(c) for c in raw_commits]
                            # Clear old commits for this repo (simple strategy for v0.1)
                            session.query(Commit).filter_by(repository_id=repo.id).delete()
                            for ci in commit_infos:
                                session.add(
                                    Commit(
                                        repository_id=repo.id,
                                        sha=ci.sha,
                                        message=ci.message,
                                        author=ci.author,
                                        author_date=ci.author_date,
                                        committer_date=ci.committer_date,
                                    )
                                )
                        except Exception as exc:  # noqa: BLE001
                            logger.debug("Commits failed for %s: %s", full_name, exc)
                            commit_infos = []

                        # Activity
                        score = calculate_activity_score(
                            commit_infos,
                            is_archived=repo.is_archived,
                            has_docs=has_documentation(paths),
                            has_tests=has_tests(paths),
                        )
                        snap = ActivitySnapshot(
                            repository_id=repo.id,
                            snapshot_date=datetime.now(timezone.utc),
                            activity_score=score.score,
                            classification=score.classification.value,
                            evidence=json.dumps(score.evidence),
                        )
                        session.add(snap)

                        if run_security:
                            try:
                                from ab_hub.services.security_service import (
                                    analyze_repository_security,
                                )

                                await analyze_repository_security(client, repo, session=session)
                            except Exception as sec_exc:  # noqa: BLE001
                                logger.debug("Security scan skipped for %s: %s", full_name, sec_exc)

                        session.commit()
                        analyzed += 1
                    except Exception as exc:  # noqa: BLE001
                        msg = f"{full_name}: {exc}"
                        errors.append(msg)
                        logger.warning("Failed to analyze %s: %s", full_name, exc)
                        session.rollback()

                    progress.advance(task)

            finish_scan(
                session,
                scan,
                discovered=discovered,
                analyzed=analyzed,
                errors=errors or None,
                status="completed" if not errors else "completed_with_errors",
            )
            session.commit()

    return {
        "discovered": discovered,
        "analyzed": analyzed,
        "errors": errors,
    }
