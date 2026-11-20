"""Helpers de tabelas Rich — design consistente."""

from __future__ import annotations

from typing import Sequence

from rich import box
from rich.table import Table

from ab_hub.storage.models import Repository


def repositories_table(repos: Sequence[Repository]) -> Table:
    """Tabela de repositórios com estilo limpo e legível."""
    table = Table(
        title="[bold cyan]Repositórios[/]",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        box=box.ROUNDED,
        title_style="bold",
        pad_edge=False,
        expand=False,
    )
    table.add_column("Nome", style="cyan", no_wrap=True)
    table.add_column("Proprietário")
    table.add_column("Visibilidade")
    table.add_column("Arquivado", justify="center")
    table.add_column("Último push")
    table.add_column("Última análise")

    for r in repos:
        visibility = r.visibility or "—"
        if visibility == "private":
            visibility = "[yellow]privado[/]"
        elif visibility == "public":
            visibility = "[green]público[/]"

        table.add_row(
            r.name,
            r.owner or "—",
            visibility,
            "[green]✓[/]" if r.is_archived else "[dim]—[/]",
            r.pushed_at.strftime("%Y-%m-%d") if r.pushed_at else "—",
            r.last_scanned_at.strftime("%Y-%m-%d %H:%M") if r.last_scanned_at else "—",
        )
    return table
