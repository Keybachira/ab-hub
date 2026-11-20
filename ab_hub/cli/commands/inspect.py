"""Comandos de inspecção e inteligência."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table
from rich import box

from ab_hub.services.comparison_service import compare_repositories
from ab_hub.services.inspection_service import inspect_repository
from ab_hub.storage.database import get_session, init_db
from ab_hub.storage.models import Repository
from sqlalchemy import select

console = Console()
app = typer.Typer(help="Inspeccionar projectos e actividade")


@app.command("ver")
def inspect_cmd(
    name: str = typer.Argument(..., help="Nome do repositório ou full_name"),
) -> None:
    """Mostrar informação detalhada sobre um repositório."""
    data = inspect_repository(name)
    if data is None:
        console.print(f"[red]Repositório não encontrado:[/] {name}")
        raise typer.Exit(1)
    console.print(Pretty(data, expand_all=True))


@app.command("actividade")
def activity_cmd(
    name: str = typer.Argument(None, help="Nome opcional do repositório"),
) -> None:
    """Mostrar pontuações de actividade."""
    init_db()
    with get_session() as session:
        if name:
            from ab_hub.storage.repositories import get_repository_by_name

            repo = get_repository_by_name(session, name)
            if not repo:
                console.print(f"[red]Não encontrado:[/] {name}")
                raise typer.Exit(1)
            snaps = sorted(repo.activity_snapshots, key=lambda s: s.snapshot_date, reverse=True)
            if not snaps:
                console.print("[yellow]Ainda não há dados de actividade.[/]")
                return
            s = snaps[0]
            console.print(f"[bold]{repo.full_name}[/]")
            console.print(f"  Pontuação      : {s.activity_score}")
            console.print(f"  Classificação  : {s.classification}")
            console.print(f"  Snapshot       : {s.snapshot_date}")
        else:
            # Visão geral
            table = Table(
                title="[bold cyan]Visão geral de actividade[/]",
                box=box.ROUNDED,
                border_style="dim",
                header_style="bold magenta",
            )
            table.add_column("Repositório", style="cyan")
            table.add_column("Pontuação", justify="right")
            table.add_column("Classificação")
            stmt = select(Repository).limit(100)
            for repo in session.execute(stmt).scalars():
                if not repo.activity_snapshots:
                    continue
                s = sorted(repo.activity_snapshots, key=lambda x: x.snapshot_date, reverse=True)[0]
                table.add_row(repo.full_name, f"{s.activity_score:.1f}", s.classification)
            console.print(table)


@app.command("abandonados")
def abandoned_cmd() -> None:
    """Listar projectos possivelmente abandonados ou dormentes."""
    init_db()
    with get_session() as session:
        table = Table(
            title="[bold yellow]Possivelmente abandonados / dormentes[/]",
            box=box.ROUNDED,
            border_style="dim",
            header_style="bold magenta",
        )
        table.add_column("Repositório", style="cyan")
        table.add_column("Pontuação", justify="right")
        table.add_column("Classificação")
        count = 0
        for repo in session.execute(select(Repository)).scalars():
            if not repo.activity_snapshots:
                continue
            s = sorted(repo.activity_snapshots, key=lambda x: x.snapshot_date, reverse=True)[0]
            if s.classification in (
                "Possivelmente abandonado",
                "Dormente",
                "Arquivado",
                "Possibly Abandoned",  # dados antigos em inglês
                "Dormant",
                "Archived",
            ):
                table.add_row(repo.full_name, f"{s.activity_score:.1f}", s.classification)
                count += 1
        if count == 0:
            console.print("[green]Nenhum projecto dormente/abandonado detectado.[/]")
        else:
            console.print(table)


@app.command("comparar")
def compare_cmd(
    a: str = typer.Argument(..., help="Primeiro repositório"),
    b: str = typer.Argument(..., help="Segundo repositório"),
) -> None:
    """Comparar dois repositórios."""
    result = compare_repositories(a, b)
    if result is None:
        console.print("[red]Um ou ambos os repositórios não foram encontrados.[/]")
        raise typer.Exit(1)
    console.print(Pretty(result, expand_all=True))


@app.command("tecnologias")
def technologies_cmd() -> None:
    """Mostrar visão geral de tecnologias em todos os repositórios."""
    from ab_hub.services.report_service import generate_summary_report

    report = generate_summary_report()
    table = Table(
        title="[bold cyan]Principais tecnologias[/]",
        box=box.ROUNDED,
        border_style="dim",
        header_style="bold magenta",
    )
    table.add_column("Tecnologia", style="cyan")
    table.add_column("Repositórios", justify="right")
    for t in report.get("top_technologies") or []:
        table.add_row(t["name"], str(t["count"]))
    console.print(table)


# Aliases em inglês
app.command("inspect")(inspect_cmd)
app.command("activity")(activity_cmd)
app.command("abandoned")(abandoned_cmd)
app.command("compare")(compare_cmd)
app.command("technologies")(technologies_cmd)
