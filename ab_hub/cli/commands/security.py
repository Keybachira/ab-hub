"""Security monitoring commands."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table

from ab_hub.core.exceptions import AuthenticationError
from ab_hub.services.security_service import (
    get_security_overview,
    list_vulnerabilities_for_repo,
    run_security_scan,
)

console = Console()
app = typer.Typer(help="Dependency vulnerability & security monitoring")


@app.callback(invoke_without_command=True)
def security_root(ctx: typer.Context) -> None:
    """Security monitoring (use subcommands or --help)."""
    if ctx.invoked_subcommand is None:
        # Default: show overview
        overview()


@app.command("scan")
def security_scan(
    repo: str = typer.Argument(None, help="Optional repository name (default: recent batch)"),
    limit: int = typer.Option(30, "--limit", "-n", help="Max repositories when scanning batch"),
) -> None:
    """Run vulnerability scan (OSV) on one or many repositories."""
    try:
        console.print("[bold]Running security scan (OSV)…[/]")
        result = asyncio.run(run_security_scan(repo_name=repo, limit=limit))
        if "error" in result:
            console.print(f"[red]{result['error']}[/]")
            raise typer.Exit(1)

        console.print(
            f"\n[green]✓ Security scan complete[/]\n"
            f"  Processed        : {result['processed']}\n"
            f"  Vulnerabilities  : {result['total_vulnerabilities']}\n"
            f"  Errors           : {len(result.get('errors') or [])}"
        )
        # Show per-repo summary table
        table = Table(title="Security results")
        table.add_column("Repository")
        table.add_column("Deps", justify="right")
        table.add_column("Vulns", justify="right")
        table.add_column("Status")
        table.add_column("Health", justify="right")
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
            console.print("\n[yellow]Errors:[/]")
            for e in result["errors"][:8]:
                console.print(f"  • {e}")
    except AuthenticationError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Security scan failed:[/] {exc}")
        raise typer.Exit(1)


@app.command("overview")
def overview() -> None:
    """Show global security posture from local database."""
    data = get_security_overview()
    console.print(Pretty(data, expand_all=False))

    by_sev = data.get("by_severity") or {}
    if by_sev:
        table = Table(title="Vulnerabilities by severity")
        table.add_column("Severity")
        table.add_column("Count", justify="right")
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


@app.command("list")
def list_vulns(
    repo: str = typer.Argument(..., help="Repository name or full_name"),
) -> None:
    """List known vulnerabilities for a specific repository."""
    vulns = list_vulnerabilities_for_repo(repo)
    if vulns is None:
        console.print(f"[red]Repository not found:[/] {repo}")
        raise typer.Exit(1)
    if not vulns:
        console.print(f"[green]No vulnerabilities recorded for[/] {repo}")
        console.print("[dim]Run: ab-hub security scan <repo>[/]")
        return

    table = Table(title=f"Vulnerabilities — {repo}")
    table.add_column("Severity")
    table.add_column("Package")
    table.add_column("Installed")
    table.add_column("Fixed")
    table.add_column("ID")
    table.add_column("Summary")

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
    console.print(f"\n[dim]{len(vulns)} finding(s)[/]")
