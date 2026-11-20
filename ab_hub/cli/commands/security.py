"""Comandos de monitorização de segurança."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table
from rich.pretty import Pretty
from rich import box

from ab_hub.core.exceptions import AuthenticationError
from ab_hub.services.security_service import (
    get_security_overview,
    list_vulnerabilities_for_repo,
    run_security_scan,
)

console = Console()
app = typer.Typer(help="Monitorização de vulnerabilidades e segurança de dependências")


@app.callback(invoke_without_command=True)
def security_root(ctx: typer.Context) -> None:
    """Monitorização de segurança (use subcomandos ou --help)."""
    if ctx.invoked_subcommand is None:
        # Por omissão: mostrar visão geral
        overview()


@app.command("analisar")
def security_scan(
    repo: str = typer.Argument(
        None, help="Nome opcional do repositório (por omissão: lote recente)"
    ),
    limit: int = typer.Option(
        30, "--limit", "-n", help="Máximo de repositórios ao analisar em lote"
    ),
) -> None:
    """Executar análise de vulnerabilidades (OSV) num ou em vários repositórios."""
    try:
        console.print("[bold]A executar análise de segurança (OSV)…[/]")
        result = asyncio.run(run_security_scan(repo_name=repo, limit=limit))
        if "error" in result:
            console.print(f"[red]{result['error']}[/]")
            raise typer.Exit(1)

        console.print(
            f"\n[green]✓ Análise de segurança concluída[/]\n"
            f"  Processados       : {result['processed']}\n"
            f"  Vulnerabilidades  : {result['total_vulnerabilities']}\n"
            f"  Erros             : {len(result.get('errors') or [])}"
        )
        # Tabela de resumo por repositório
        table = Table(
            title="[bold cyan]Resultados de segurança[/]",
            box=box.ROUNDED,
            border_style="dim",
            header_style="bold magenta",
        )
        table.add_column("Repositório", style="cyan")
        table.add_column("Deps", justify="right")
        table.add_column("Vulns", justify="right")
        table.add_column("Estado")
        table.add_column("Saúde", justify="right")
        for r in result.get("results") or []:
            summary = r.get("summary") or {}
            table.add_row(
                r.get("repository", "?"),
                str(r.get("dependencies", 0)),
                str(r.get("vulnerabilities", 0)),
                summary.get("status", "—"),
                str(summary.get("health_score", "—")),
            )
        if result.get("results"):
            console.print(table)
        if result.get("errors"):
            console.print("\n[yellow]Erros:[/]")
            for e in result["errors"][:8]:
                console.print(f"  • {e}")
    except AuthenticationError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]A análise de segurança falhou:[/] {exc}")
        raise typer.Exit(1)


@app.command("resumo")
def overview() -> None:
    """Mostrar a postura de segurança global a partir da base de dados local."""
    data = get_security_overview()
    console.print(Pretty(data, expand_all=False))

    by_sev = data.get("by_severity") or {}
    if by_sev:
        table = Table(
            title="[bold cyan]Vulnerabilidades por gravidade[/]",
            box=box.ROUNDED,
            border_style="dim",
            header_style="bold magenta",
        )
        table.add_column("Gravidade")
        table.add_column("Quantidade", justify="right")
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"):
            if sev in by_sev:
                style = {
                    "CRITICAL": "bold red",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "dim",
                }.get(sev, "")
                table.add_row(sev, str(by_sev[sev]), style=style)
        console.print(table)


@app.command("listar")
def list_vulns(
    repo: str = typer.Argument(..., help="Nome do repositório ou full_name"),
) -> None:
    """Listar vulnerabilidades conhecidas de um repositório específico."""
    vulns = list_vulnerabilities_for_repo(repo)
    if vulns is None:
        console.print(f"[red]Repositório não encontrado:[/] {repo}")
        raise typer.Exit(1)
    if not vulns:
        console.print(f"[green]Nenhuma vulnerabilidade registada para[/] {repo}")
        console.print("[dim]Execute: ab-hub seguranca analisar <repo>[/]")
        return

    table = Table(
        title=f"[bold cyan]Vulnerabilidades — {repo}[/]",
        box=box.ROUNDED,
        border_style="dim",
        header_style="bold magenta",
    )
    table.add_column("Gravidade")
    table.add_column("Pacote")
    table.add_column("Instalada")
    table.add_column("Corrigida")
    table.add_column("ID")
    table.add_column("Resumo")

    for v in vulns:
        sev = v.get("severity") or "UNKNOWN"
        style = {
            "CRITICAL": "bold red",
            "HIGH": "red",
            "MEDIUM": "yellow",
        }.get(sev, "")
        vid = v.get("cve_id") or v.get("ghsa_id") or v.get("osv_id") or "—"
        table.add_row(
            sev,
            v.get("package") or "—",
            v.get("installed_version") or "—",
            v.get("fixed_version") or "—",
            vid,
            (v.get("summary") or "")[:60],
            style=style,
        )
    console.print(table)
    console.print(f"\n[dim]{len(vulns)} resultado(s)[/]")


# Aliases em inglês
app.command("scan")(security_scan)
app.command("overview")(overview)
app.command("list")(list_vulns)
