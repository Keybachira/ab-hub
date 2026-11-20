"""Banner ASCII, ecrã de boas-vindas e helpers partilhados de UI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

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
    """Mostra o banner principal do AB-hub."""
    console = console or Console()
    console.print(BANNER)
    console.print(
        Panel(
            Text.from_markup(
                f"[bold]SISTEMA DE INTELIGÊNCIA DE PROJECTOS[/]  ·  v{__version__}\n"
                f"[dim]Sabe o que construiu. Controla o que possui.[/]"
            ),
            border_style="cyan",
            padding=(0, 2),
            box=box.ROUNDED,
        )
    )


def print_home(
    console: Console | None = None,
    *,
    account: str | None = None,
    connected: bool = False,
) -> None:
    """Ecrã inicial amigável quando o utilizador corre `ab-hub` sem comando."""
    console = console or Console()
    print_banner(console)
    console.print()

    if connected and account:
        status_markup = f"[bold green]● LIGADO[/]  como [bold cyan]{account}[/]"
        border = "green"
    else:
        status_markup = (
            "[bold yellow]○ NÃO LIGADO[/]  — execute [cyan]ab-hub autenticacao entrar[/]"
        )
        border = "yellow"

    console.print(
        Panel(
            Text.from_markup(status_markup),
            border_style=border,
            padding=(0, 2),
            box=box.ROUNDED,
        )
    )
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2), expand=False)
    table.add_column(style="bold cyan", min_width=34)
    table.add_column(style="dim")

    table.add_row("ab-hub autenticacao entrar", "Ligar a sua conta GitHub")
    table.add_row("ab-hub analisar", "Descobrir e analisar repositórios")
    table.add_row("ab-hub listar", "Ver o inventário de projectos")
    table.add_row("ab-hub inspeccionar ver <nome>", "Análise detalhada de um projecto")
    table.add_row("ab-hub seguranca analisar", "Verificar vulnerabilidades")
    table.add_row("ab-hub abandonados", "Encontrar projectos abandonados")
    table.add_row("ab-hub relatorio gerar", "Relatório de inteligência")
    table.add_row("ab-hub exportar -f json", "Exportar dados")

    console.print(
        Panel(
            table,
            title="[bold]Comandos rápidos[/]",
            title_align="left",
            border_style="cyan",
            padding=(0, 1),
            box=box.ROUNDED,
        )
    )
    console.print()
    console.print(
        "[dim]Dica:[/] use  [cyan]ab-hub <comando> --help[/]  para ver as opções"
    )
    console.print()


def success_panel(message: str, title: str = "Sucesso") -> Panel:
    return Panel(
        Text.from_markup(message),
        title=f"[bold green]✓ {title}[/]",
        border_style="green",
        padding=(1, 2),
        box=box.ROUNDED,
    )


def error_panel(message: str, title: str = "Erro") -> Panel:
    return Panel(
        Text.from_markup(message),
        title=f"[bold red]✗ {title}[/]",
        border_style="red",
        padding=(1, 2),
        box=box.ROUNDED,
    )


def warning_panel(message: str, title: str = "Aviso") -> Panel:
    return Panel(
        Text.from_markup(message),
        title=f"[bold yellow]⚠ {title}[/]",
        border_style="yellow",
        padding=(1, 2),
        box=box.ROUNDED,
    )


def info_panel(message: str, title: str = "Info") -> Panel:
    return Panel(
        Text.from_markup(message),
        title=f"[bold cyan]ℹ {title}[/]",
        border_style="cyan",
        padding=(1, 2),
        box=box.ROUNDED,
    )
