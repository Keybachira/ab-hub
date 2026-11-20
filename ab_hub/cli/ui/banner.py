"""ASCII banner, welcome screen and shared UI helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ab_hub import __version__

BANNER = r"""[bold cyan]
  █████╗ ██████╗       ██╗  ██╗██╗   ██╗██████╗
 ██╔══██╗██╔══██╗      ██║  ██║██║   ██║██╔══██╗
 ███████║██████╔╝█████╗███████║██║   ██║██████╔╝
 ██╔══██║██╔══██╗╚════╝██╔══██║██║   ██║██╔══██╗
 ██║  ██║██████╔╝      ██║  ██║╚██████╔╝██████╔╝
 ╚═╝  ╚═╝╚═════╝       ╚═╝  ╚═╝ ╚═════╝ ╚═════╝
[/]"""


def print_banner(console: Console | None = None) -> None:
    console = console or Console()
    console.print(BANNER)
    console.print(
        Panel(
            Text.from_markup(
                f"[bold]PROJECT INTELLIGENCE SYSTEM[/]  ·  v{__version__}\n"
                f"[dim]Know what you built. Control what you own.[/]"
            ),
            border_style="cyan",
            padding=(0, 2),
        )
    )


def print_home(
    console: Console | None = None, *, account: str | None = None, connected: bool = False
) -> None:
    """Friendly home screen when the user runs `ab-hub` with no command."""
    console = console or Console()
    print_banner(console)
    console.print()

    status_line = (
        f"[green]● CONNECTED[/]  as [bold]{account}[/]"
        if connected and account
        else "[yellow]○ NOT CONNECTED[/]  — run [cyan]ab-hub auth login[/]"
    )
    console.print(Panel(status_line, border_style="dim", padding=(0, 2)))
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold cyan", width=28)
    table.add_column(style="dim")
    table.add_row("ab-hub auth login", "Connect your GitHub account")
    table.add_row("ab-hub scan", "Discover & analyze repositories")
    table.add_row("ab-hub list", "Browse your inventory")
    table.add_row("ab-hub inspect <name>", "Deep dive into a project")
    table.add_row("ab-hub security scan", "Dependency vulnerability check")
    table.add_row("ab-hub abandoned", "Find dormant / abandoned projects")
    table.add_row("ab-hub report", "Summary intelligence report")
    table.add_row("ab-hub export -f json", "Export data")

    console.print(Panel(table, title="Quick commands", border_style="cyan", padding=(0, 1)))
    console.print()
    console.print("[dim]Tip: use  ab-hub <command> --help  for options[/]")
    console.print()
