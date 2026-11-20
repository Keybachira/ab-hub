"""Comando de listagem de repositórios."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich import box

from ab_hub.cli.ui.tables import repositories_table
from ab_hub.storage.database import get_session, init_db
from ab_hub.storage.repositories import list_repositories

console = Console()
app = typer.Typer(help="Listar e filtrar repositórios")


@app.callback(invoke_without_command=True)
def list_cmd(
    visibility: str = typer.Option(
        None, "--visibility", "-v", help="público | privado (public | private)"
    ),
    archived: bool = typer.Option(False, "--archived", help="Mostrar apenas repositórios arquivados"),
    owner: str = typer.Option(None, "--owner", "-o", help="Filtrar pelo login do proprietário"),
    limit: int = typer.Option(50, "--limit", "-n", help="Número máximo de resultados"),
) -> None:
    """Listar os repositórios descobertos."""
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
                    "[yellow]Nenhum repositório encontrado.[/]\n\n"
                    "Execute [bold cyan]ab-hub analisar[/] primeiro para descobrir os seus projectos.",
                    border_style="yellow",
                    padding=(1, 2),
                    box=box.ROUNDED,
                )
            )
            console.print()
            return
        console.print()
        console.print(repositories_table(repos))
        console.print(f"\n[dim]A mostrar {len(repos)} repositório(s)[/]\n")
