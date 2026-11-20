"""Shell interactivo do AB-hub — permanece aberto até q + Enter."""

from __future__ import annotations

import shlex
from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ab_hub import __version__
from ab_hub.cli.ui.banner import print_banner
from ab_hub.github.authentication import get_token

console = Console()

# Comandos internos do shell (não passam pelo Typer)
QUIT_WORDS = {"q", "quit", "sair", "exit", "fechar"}
HELP_WORDS = {"ajuda", "help", "?"}
CLEAR_WORDS = {"limpar", "clear", "cls"}


def _resolve_account() -> tuple[str | None, bool]:
    """Tenta obter o utilizador ligado (best-effort)."""
    token = get_token()
    if not token:
        return None, False
    try:
        import asyncio

        from ab_hub.github.client import GitHubClient

        async def _who() -> str | None:
            async with GitHubClient() as client:
                user = await client.get_authenticated_user()
                return user.get("login")

        return asyncio.run(_who()), True
    except Exception:
        return "…", True


def _print_status_bar(account: str | None, connected: bool) -> None:
    if connected and account:
        line = f"[bold green]● LIGADO[/]  [cyan]{account}[/]  ·  v{__version__}"
        style = "green"
    else:
        line = f"[bold yellow]○ NÃO LIGADO[/]  ·  v{__version__}  ·  [dim]autenticacao entrar[/]"
        style = "yellow"
    console.print(Panel(Text.from_markup(line), border_style=style, padding=(0, 2), box=box.ROUNDED))


def _print_help() -> None:
    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        border_style="dim",
        title="[bold cyan]Comandos disponíveis[/]",
        title_style="bold",
    )
    table.add_column("Comando", style="bold cyan", min_width=28)
    table.add_column("Descrição", style="dim")

    rows = [
        ("autenticacao entrar", "Ligar conta GitHub"),
        ("autenticacao estado", "Ver estado da sessão"),
        ("autenticacao sair", "Terminar sessão"),
        ("analisar", "Descobrir e analisar repositórios"),
        ("analisar --security", "Análise + vulnerabilidades"),
        ("listar", "Inventário de projectos"),
        ("inspeccionar ver <nome>", "Detalhe de um projecto"),
        ("actividade", "Pontuações de actividade"),
        ("abandonados", "Projectos dormentes/abandonados"),
        ("comparar <a> <b>", "Comparar dois repositórios"),
        ("tecnologias", "Tecnologias em uso"),
        ("seguranca analisar", "Scan de vulnerabilidades"),
        ("seguranca resumo", "Postura de segurança"),
        ("seguranca listar <repo>", "Vulns de um repositório"),
        ("relatorio gerar", "Relatório de inteligência"),
        ("exportar -f json", "Exportar dados"),
        ("ajuda", "Mostrar esta lista"),
        ("limpar", "Limpar o ecrã"),
        ("q", "Sair do AB-hub"),
    ]
    for cmd, desc in rows:
        table.add_row(cmd, desc)

    console.print()
    console.print(table)
    console.print()
    console.print(
        "[dim]Também funcionam os nomes em inglês (auth, scan, list, …).[/]"
    )
    console.print()


def _print_welcome(account: str | None, connected: bool) -> None:
    print_banner(console)
    console.print()
    _print_status_bar(account, connected)
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                "[bold]Shell interactivo[/]\n"
                "Escreva um comando e prima Enter.\n"
                "Digite [cyan]ajuda[/] para a lista · [cyan]q[/] + Enter para sair."
            ),
            border_style="cyan",
            padding=(1, 2),
            box=box.ROUNDED,
        )
    )
    console.print()


def _dispatch(line: str, typer_app: Callable[..., None]) -> None:
    """Executa uma linha de comando no Typer app."""
    try:
        args = shlex.split(line)
    except ValueError as exc:
        console.print(f"[red]✗[/] Linha inválida: {exc}")
        return

    if not args:
        return

    try:
        # standalone_mode=False evita SystemExit e deixa o shell continuar
        typer_app(args, standalone_mode=False)
    except SystemExit as exc:
        # Typer/Click pode ainda levantar SystemExit em alguns caminhos
        code = exc.code
        if code not in (0, None):
            console.print(f"[dim](código de saída: {code})[/]")
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]✗ Erro:[/] {exc}")


def run_interactive_shell(typer_app: Callable[..., None]) -> None:
    """
    Loop principal do shell.

    O utilizador permanece dentro do CLI até escrever q / sair / exit + Enter.
    """
    account, connected = _resolve_account()
    _print_welcome(account, connected)

    while True:
        try:
            # Prompt estilizado
            raw = console.input("[bold cyan]ab-hub[/][dim] › [/]")
        except (EOFError, KeyboardInterrupt):
            console.print()
            console.print("[dim]A sair…[/]")
            break

        line = (raw or "").strip()
        if not line:
            continue

        low = line.lower()

        # --- comandos internos do shell ---
        if low in QUIT_WORDS:
            console.print()
            console.print(
                Panel(
                    "[green]Sessão terminada. Até à próxima.[/]",
                    border_style="green",
                    padding=(0, 2),
                    box=box.ROUNDED,
                )
            )
            console.print()
            break

        if low in HELP_WORDS:
            _print_help()
            continue

        if low in CLEAR_WORDS:
            console.clear()
            print_banner(console)
            console.print()
            _print_status_bar(account, connected)
            console.print()
            continue

        # Recarregar estado após login/logout
        if low.startswith("autenticacao ") or low.startswith("auth "):
            _dispatch(line, typer_app)
            account, connected = _resolve_account()
            console.print()
            continue

        _dispatch(line, typer_app)
        console.print()
