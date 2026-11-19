"""Rich table helpers."""

from __future__ import annotations

from typing import Sequence

from rich.table import Table

from ab_hub.storage.models import Repository


def repositories_table(repos: Sequence[Repository]) -> Table:
    table = Table(
        title="Repositories",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        title_style="bold cyan",
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Owner")
    table.add_column("Visibility")
    table.add_column("Archived", justify="center")
    table.add_column("Pushed")
    table.add_column("Last scan")

    for r in repos:
        table.add_row(
            r.name,
            r.owner,
            r.visibility,
            "✓" if r.is_archived else "—",
            r.pushed_at.strftime("%Y-%m-%d") if r.pushed_at else "—",
            r.last_scanned_at.strftime("%Y-%m-%d %H:%M") if r.last_scanned_at else "—",
        )
    return table
