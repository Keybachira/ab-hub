"""List repositories command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from ab_hub.cli.ui.tables import repositories_table
from ab_hub.storage.database import get_session, init_db
from ab_hub.storage.repositories import list_repositories

console = Console()
app = typer.Typer(help="List and filter repositories")


@app.callback(invoke_without_command=True)
def list_cmd(
    visibility: str = typer.Option(None, "--visibility", "-v", help="public | private"),
    archived: bool = typer.Option(False, "--archived", help="Show only archived repositories"),
    owner: str = typer.Option(None, "--owner", "-o", help="Filter by owner login"),
    limit: int = typer.Option(50, "--limit", "-n", help="Max results"),
) -> None:
    """List discovered repositories."""
    init_db()
    with get_session() as session:
        repos = list_repositories(
            session,
            visibility=visibility,
            archived=True if archived else None,
            owner=owner,
            limit=limit,
        )
        if not repos:
            console.print()
            console.print(
                Panel(
                    "[yellow]No repositories found.[/]\n\n"
                    "Run [bold cyan]ab-hub scan[/] first to discover your projects.",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )
            console.print()
            return
        console.print()
        console.print(repositories_table(repos))
        console.print(f"\n[dim]Showing {len(repos)} repositories[/]\n")
