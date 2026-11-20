"""Comandos de autenticação — limpos, resilientes e amigáveis."""

from __future__ import annotations

import asyncio
import re

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ab_hub.core.exceptions import AuthenticationError, GitHubAPIError
from ab_hub.github.authentication import (
    delete_token,
    get_token,
    set_token,
    token_source,
)
from ab_hub.github.client import GitHubClient

console = Console()
app = typer.Typer(help="Autenticação — login, estado e logout")


def _looks_like_token(value: str) -> bool:
    value = value.strip()
    if len(value) < 20:
        return False
    # PAT clássico, fine-grained ou estilo OAuth
    return bool(
        re.match(r"^(ghp_|github_pat_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]+$", value)
        or (len(value) >= 40 and " " not in value)
    )


@app.command("entrar")
def login(
    token: str = typer.Option(
        None,
        "--token",
        "-t",
        help="Token de Acesso Pessoal do GitHub (omitir para introduzir interactivamente)",
        hide_input=True,
    ),
) -> None:
    """
    Autenticar-se no GitHub.

    Crie um token em: https://github.com/settings/tokens
    Âmbitos recomendados: repo, read:org
    """
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                "[bold]Login AB-hub[/]\n\n"
                "Precisa de um [cyan]Token de Acesso Pessoal do GitHub[/].\n"
                "Crie um em: [link=https://github.com/settings/tokens]"
                "https://github.com/settings/tokens[/link]\n\n"
                "[dim]Âmbitos recomendados:[/]  [green]repo[/]  ·  [green]read:org[/]\n"
                "[dim]Tokens fine-grained também funcionam (Contents: Read + Metadata).[/]"
            ),
            title="🔐 Autenticação",
            border_style="cyan",
            padding=(1, 2),
            box=box.ROUNDED,
        )
    )
    console.print()

    if not token:
        try:
            token = typer.prompt("Cole o seu token GitHub", hide_input=True)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Login cancelado.[/]")
            raise typer.Exit(0)

    token = (token or "").strip()
    if not token:
        console.print("[red]✗[/] Token vazio. Nada foi guardado.")
        raise typer.Exit(1)

    if not _looks_like_token(token):
        console.print(
            "[yellow]⚠[/] O formato do token parece invulgar. "
            "A continuar na mesma — o GitHub irá validá-lo."
        )

    # Guardar primeiro (para poder limpar em caso de falha se quisermos)
    try:
        backend = set_token(token)
    except AuthenticationError as exc:
        console.print(f"[red]✗[/] Não foi possível guardar o token: {exc}")
        raise typer.Exit(1)

    # Validar contra o GitHub
    console.print("[dim]A validar o token com o GitHub…[/]")

    async def _validate() -> dict:
        async with GitHubClient(token=token) as client:
            user = await client.get_authenticated_user()
            try:
                rate = await client.get_rate_limit()
            except Exception:
                rate = {}
            return {"user": user, "rate": rate}

    try:
        data = asyncio.run(_validate())
    except GitHubAPIError as exc:
        # Não deixar um token inválido guardado se a validação falhar por auth
        if getattr(exc, "status_code", None) in (401, 403):
            delete_token()
            console.print(
                Panel(
                    f"[red]Autenticação falhou[/]\n\n{exc}\n\n"
                    "[dim]O token não foi guardado. Verifique os âmbitos e a validade.[/]",
                    border_style="red",
                    title="✗ Login falhou",
                    box=box.ROUNDED,
                )
            )
            raise typer.Exit(1)
        console.print(f"[yellow]⚠[/] Token guardado, mas a verificação da API teve um problema: {exc}")
        console.print(f"[green]✓[/] Token guardado via [bold]{backend}[/]")
        raise typer.Exit(0)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]⚠[/] Erro de rede/validação: {exc}")
        console.print(
            f"[green]✓[/] O token foi mesmo assim guardado via [bold]{backend}[/]. "
            "Execute [cyan]ab-hub autenticacao estado[/] mais tarde para confirmar."
        )
        raise typer.Exit(0)

    user = data["user"]
    rate = data.get("rate") or {}
    core = rate.get("resources", {}).get("core", {})

    login_name = user.get("login", "?")
    name = user.get("name") or ""
    remaining = core.get("remaining", "?")
    limit = core.get("limit", "?")

    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"[bold green]✓ Login efectuado com sucesso[/]\n\n"
                f"[bold]Utilizador[/]  {login_name}"
                + (f"  ([dim]{name}[/])" if name else "")
                + f"\n[bold]Armazenamento[/]  {backend}\n"
                f"[bold]Limite API[/]  {remaining}/{limit} restantes"
            ),
            border_style="green",
            title="Bem-vindo",
            padding=(1, 2),
            box=box.ROUNDED,
        )
    )
    console.print()
    console.print("[dim]Próximo passo:[/]  [cyan]ab-hub analisar[/]  — descobrir os seus repositórios")
    console.print()


@app.command("estado")
def status() -> None:
    """Mostrar o estado actual de autenticação e os limites de taxa."""
    token = get_token()
    source = token_source()

    if not token:
        console.print()
        console.print(
            Panel(
                Text.from_markup(
                    "[yellow]Não autenticado[/]\n\n"
                    "Execute [bold cyan]ab-hub autenticacao entrar[/] para ligar a sua conta GitHub.\n"
                    "Ou defina [bold]GITHUB_TOKEN[/] no ambiente."
                ),
                border_style="yellow",
                title="Estado",
                padding=(1, 2),
                box=box.ROUNDED,
            )
        )
        console.print()
        raise typer.Exit(1)

    console.print("[dim]A verificar a ligação ao GitHub…[/]")

    async def _check() -> dict:
        async with GitHubClient() as client:
            user = await client.get_authenticated_user()
            rate = await client.get_rate_limit()
            return {"user": user, "rate": rate}

    try:
        data = asyncio.run(_check())
    except Exception as exc:  # noqa: BLE001
        console.print()
        console.print(
            Panel(
                Text.from_markup(
                    f"[red]Token encontrado, mas a verificação da API falhou[/]\n\n"
                    f"{exc}\n\n"
                    f"[dim]Origem: {source}[/]\n"
                    "Tente [cyan]ab-hub autenticacao sair[/] e depois [cyan]ab-hub autenticacao entrar[/]."
                ),
                border_style="red",
                title="✗ Estado",
                padding=(1, 2),
                box=box.ROUNDED,
            )
        )
        raise typer.Exit(1)

    user = data["user"]
    rate = data["rate"]
    core = rate.get("resources", {}).get("core", {})
    search = rate.get("resources", {}).get("search", {})

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Utilizador", f"[cyan]{user.get('login')}[/]")
    if user.get("name"):
        table.add_row("Nome", str(user.get("name")))
    table.add_row("Origem do token", source)
    table.add_row("Limite core", f"{core.get('remaining', '?')} / {core.get('limit', '?')}")
    table.add_row("Limite search", f"{search.get('remaining', '?')} / {search.get('limit', '?')}")
    if user.get("html_url"):
        table.add_row("Perfil", user["html_url"])

    console.print()
    console.print(
        Panel(
            table,
            title="[green]✓ Ligado[/]",
            border_style="green",
            padding=(1, 1),
            box=box.ROUNDED,
        )
    )
    console.print()


@app.command("sair")
def logout() -> None:
    """Remover as credenciais guardadas."""
    had = get_token() is not None
    delete_token()
    console.print()
    if had:
        console.print(
            Panel(
                "[green]✓[/] Sessão terminada. Credenciais removidas do keyring e da configuração local.",
                border_style="green",
                padding=(0, 2),
                box=box.ROUNDED,
            )
        )
    else:
        console.print(
            Panel(
                "[dim]Nenhuma credencial guardada encontrada. Já estava desligado.[/]",
                border_style="dim",
                padding=(0, 2),
                box=box.ROUNDED,
            )
        )
    console.print()


# Aliases em inglês
app.command("login")(login)
app.command("status")(status)
app.command("logout")(logout)
