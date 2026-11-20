"""Comandos de análise (scan)."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich import box

from ab_hub.core.exceptions import AuthenticationError
from ab_hub.services.scan_service import run_full_scan

console = Console()
app = typer.Typer(help="Descoberta e sincronização de repositórios")


@app.callback(invoke_without_command=True)
def scan(
    ctx: typer.Context,
    incremental: bool = typer.Option(
        False, "--incremental", "-i", help="Processar apenas alterações"
    ),
    full: bool = typer.Option(False, "--full", help="Forçar reanálise completa"),
    all_repos: bool = typer.Option(False, "--all", help="Alias para descoberta completa"),
    security: bool = typer.Option(
        False,
        "--security",
        "-S",
        help="Executar também a análise de vulnerabilidades de dependências (OSV)",
    ),
) -> None:
    """Descobrir e analisar os repositórios GitHub acessíveis."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        console.print()
        console.print("[bold cyan]▶ A iniciar análise[/]")
        if security:
            console.print("[dim]  Monitorização de segurança activada (OSV)[/]")
        console.print()
        result = asyncio.run(
            run_full_scan(
                incremental=incremental and not full,
                run_security=security,
            )
        )
        console.print()
        console.print(
            Panel(
                f"[green]✓ Análise concluída[/]\n\n"
                f"  Descobertos  : [bold]{result['discovered']}[/]\n"
                f"  Analisados   : [bold]{result['analyzed']}[/]\n"
                f"  Erros        : {len(result['errors'])}",
                border_style="green",
                padding=(1, 2),
                box=box.ROUNDED,
            )
        )
        if result["errors"]:
            console.print("\n[yellow]Erros:[/]")
            for e in result["errors"][:10]:
                console.print(f"  • {e}")
            if len(result["errors"]) > 10:
                console.print(f"  … e mais {len(result['errors']) - 10}")
        console.print()
    except AuthenticationError as exc:
        console.print()
        console.print(
            Panel(
                str(exc),
                title="Autenticação necessária",
                border_style="red",
                padding=(1, 2),
                box=box.ROUNDED,
            )
        )
        console.print()
        raise typer.Exit(1)
    except Exception as exc:  # noqa: BLE001
        console.print()
        console.print(
            Panel(
                f"[red]A análise falhou[/]\n\n{exc}",
                border_style="red",
                padding=(1, 2),
                box=box.ROUNDED,
            )
        )
        console.print()
        raise typer.Exit(1)
