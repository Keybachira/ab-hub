"""Inspection and intelligence commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table

from ab_hub.services.comparison_service import compare_repositories
from ab_hub.services.inspection_service import inspect_repository
from ab_hub.storage.database import get_session, init_db
from ab_hub.storage.models import ActivitySnapshot, Repository
from sqlalchemy import select

console = Console()
app = typer.Typer(help="Inspect projects and activity")


@app.command("inspect")
def inspect_cmd(name: str = typer.Argument(..., help="Repository name or full_name")) -> None:
    """Show detailed information about a repository."""
    data = inspect_repository(name)
    if data is None:
        console.print(f"[red]Repository not found:[/] {name}")
        raise typer.Exit(1)
    console.print(Pretty(data, expand_all=True))


@app.command("activity")
def activity_cmd(
    name: str = typer.Argument(None, help="Optional repository name"),
) -> None:
    """Show activity scores."""
    init_db()
    with get_session() as session:
        if name:
            from ab_hub.storage.repositories import get_repository_by_name
            repo = get_repository_by_name(session, name)
            if not repo:
                console.print(f"[red]Not found:[/] {name}")
                raise typer.Exit(1)
            snaps = sorted(repo.activity_snapshots, key=lambda s: s.snapshot_date, reverse=True)
            if not snaps:
                console.print("[yellow]No activity data yet.[/]")
                return
            s = snaps[0]
            console.print(f"[bold]{repo.full_name}[/]")
            console.print(f"  Score          : {s.activity_score}")
            console.print(f"  Classification : {s.classification}")
            console.print(f"  Snapshot       : {s.snapshot_date}")
        else:
            # Overview
            table = Table(title="Activity Overview")
            table.add_column("Repository")
            table.add_column("Score", justify="right")
            table.add_column("Classification")
            stmt = select(Repository).limit(100)
            for repo in session.execute(stmt).scalars():
                if not repo.activity_snapshots:
                    continue
                s = sorted(repo.activity_snapshots, key=lambda x: x.snapshot_date, reverse=True)[0]
                table.add_row(repo.full_name, f"{s.activity_score:.1f}", s.classification)
            console.print(table)


@app.command("abandoned")
def abandoned_cmd() -> None:
    """List possibly abandoned or dormant projects."""
    init_db()
    with get_session() as session:
        table = Table(title="Potentially Abandoned / Dormant")
        table.add_column("Repository")
        table.add_column("Score", justify="right")
        table.add_column("Classification")
        count = 0
        for repo in session.execute(select(Repository)).scalars():
            if not repo.activity_snapshots:
                continue
            s = sorted(repo.activity_snapshots, key=lambda x: x.snapshot_date, reverse=True)[0]
            if s.classification in ("Possibly Abandoned", "Dormant", "Archived"):
                table.add_row(repo.full_name, f"{s.activity_score:.1f}", s.classification)
                count += 1
        if count == 0:
            console.print("[green]No dormant/abandoned projects detected.[/]")
        else:
            console.print(table)


@app.command("compare")
def compare_cmd(
    a: str = typer.Argument(..., help="First repository"),
    b: str = typer.Argument(..., help="Second repository"),
) -> None:
    """Compare two repositories."""
    result = compare_repositories(a, b)
    if result is None:
        console.print("[red]One or both repositories not found.[/]")
        raise typer.Exit(1)
    console.print(Pretty(result, expand_all=True))


@app.command("technologies")
def technologies_cmd() -> None:
    """Show technology overview across all repositories."""
    from ab_hub.services.report_service import generate_summary_report

    report = generate_summary_report()
    table = Table(title="Top Technologies")
    table.add_column("Technology")
    table.add_column("Repositories", justify="right")
    for t in report.get("top_technologies") or []:
        table.add_row(t["name"], str(t["count"]))
    console.print(table)
