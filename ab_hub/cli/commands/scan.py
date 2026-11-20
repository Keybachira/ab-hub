"""Scan commands."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

from ab_hub.core.exceptions import AuthenticationError
from ab_hub.services.scan_service import run_full_scan

console = Console()
app = typer.Typer(help="Discovery and synchronization")


@app.callback(invoke_without_command=True)
def scan(
    ctx: typer.Context,
    incremental: bool = typer.Option(False, "--incremental", "-i", help="Only process changes"),
    full: bool = typer.Option(False, "--full", help="Force full re-analysis"),
    all_repos: bool = typer.Option(False, "--all", help="Alias for full discovery"),
    security: bool = typer.Option(
        False,
        "--security",
        "-S",
        help="Also run dependency vulnerability scan (OSV)",
    ),
) -> None:
    """Discover and analyze accessible GitHub repositories."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        console.print()
        console.print("[bold cyan]▶ Starting scan[/]")
        if security:
            console.print("[dim]  Security monitoring enabled (OSV)[/]")
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
                f"[green]✓ Scan complete[/]\n\n"
                f"  Discovered : [bold]{result['discovered']}[/]\n"
                f"  Analyzed   : [bold]{result['analyzed']}[/]\n"
                f"  Errors     : {len(result['errors'])}",
                border_style="green",
                padding=(1, 2),
            )
        )
        if result["errors"]:
            console.print("\n[yellow]Errors:[/]")
            for e in result["errors"][:10]:
                console.print(f"  • {e}")
            if len(result["errors"]) > 10:
                console.print(f"  … and {len(result['errors']) - 10} more")
        console.print()
    except AuthenticationError as exc:
        console.print()
        console.print(
            Panel(str(exc), title="Authentication required", border_style="red", padding=(1, 2))
        )
        console.print()
        raise typer.Exit(1)
    except Exception as exc:  # noqa: BLE001
        console.print()
        console.print(Panel(f"[red]Scan failed[/]\n\n{exc}", border_style="red", padding=(1, 2)))
        console.print()
        raise typer.Exit(1)
