"""Report and export commands."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.pretty import Pretty

from ab_hub.exporters.csv import export_repositories_csv
from ab_hub.exporters.json import export_json
from ab_hub.exporters.markdown import export_summary_markdown
from ab_hub.services.inspection_service import inspect_repository
from ab_hub.services.report_service import generate_summary_report
from ab_hub.storage.database import get_session, init_db
from ab_hub.storage.repositories import list_repositories

console = Console()
app = typer.Typer(help="Reports and export")


@app.command("report")
def report_cmd() -> None:
    """Generate a summary intelligence report."""
    report = generate_summary_report()
    console.print(Pretty(report, expand_all=True))


@app.command("export")
def export_cmd(
    format: str = typer.Option("json", "--format", "-f", help="json | csv | markdown"),
    output: Path = typer.Option(Path("./data/export"), "--output", "-o", help="Output path prefix"),
) -> None:
    """Export data to JSON, CSV or Markdown."""
    init_db()
    format = format.lower()
    if format == "json":
        report = generate_summary_report()
        with get_session() as session:
            repos = list_repositories(session, limit=10000)
            data = {
                "summary": report,
                "repositories": [
                    {
                        "full_name": r.full_name,
                        "owner": r.owner,
                        "visibility": r.visibility,
                        "is_archived": r.is_archived,
                        "pushed_at": r.pushed_at.isoformat() if r.pushed_at else None,
                        "last_scanned_at": r.last_scanned_at.isoformat()
                        if r.last_scanned_at
                        else None,
                    }
                    for r in repos
                ],
            }
        path = export_json(data, output.with_suffix(".json"))
        console.print(f"[green]✓[/] Exported JSON → {path}")
    elif format == "csv":
        with get_session() as session:
            repos = list_repositories(session, limit=10000)
            rows = [
                {
                    "full_name": r.full_name,
                    "owner": r.owner,
                    "visibility": r.visibility,
                    "is_private": r.is_private,
                    "is_archived": r.is_archived,
                    "is_fork": r.is_fork,
                    "pushed_at": r.pushed_at.isoformat() if r.pushed_at else "",
                    "last_scanned_at": r.last_scanned_at.isoformat() if r.last_scanned_at else "",
                }
                for r in repos
            ]
        path = export_repositories_csv(rows, output.with_suffix(".csv"))
        console.print(f"[green]✓[/] Exported CSV → {path}")
    elif format == "markdown":
        report = generate_summary_report()
        path = export_summary_markdown(report, output.with_suffix(".md"))
        console.print(f"[green]✓[/] Exported Markdown → {path}")
    else:
        console.print("[red]Unsupported format. Use json, csv or markdown.[/]")
        raise typer.Exit(1)
