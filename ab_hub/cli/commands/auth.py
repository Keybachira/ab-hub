"""Authentication commands — clean, resilient, user-friendly."""

from __future__ import annotations

import asyncio
import re

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ab_hub.core.exceptions import AuthenticationError, GitHubAPIError
from ab_hub.github.authentication import (
    delete_token,
    get_token,
    set_token,
    token_source,
)
from ab_hub.github.client import GitHubClient

console = Console()
app = typer.Typer(help="Authentication — login, status, logout")


def _looks_like_token(value: str) -> bool:
    value = value.strip()
    if len(value) < 20:
        return False
    # Classic PAT, fine-grained, or OAuth-style
    return bool(
        re.match(r"^(ghp_|github_pat_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]+$", value)
        or (len(value) >= 40 and " " not in value)
    )


@app.command("login")
def login(
    token: str = typer.Option(
        None,
        "--token",
        "-t",
        help="GitHub Personal Access Token (omit to type interactively)",
        hide_input=True,
    ),
) -> None:
    """
    Authenticate with GitHub.

    Create a token at: https://github.com/settings/tokens
    Recommended scopes: repo, read:org
    """
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                "[bold]AB-hub Login[/]\n\n"
                "You need a [cyan]GitHub Personal Access Token[/].\n"
                "Create one at: [link=https://github.com/settings/tokens]"
                "https://github.com/settings/tokens[/link]\n\n"
                "[dim]Recommended scopes:[/]  [green]repo[/]  ·  [green]read:org[/]\n"
                "[dim]Fine-grained tokens also work (Contents: Read + Metadata).[/]"
            ),
            title="🔐 Authentication",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()

    if not token:
        try:
            token = typer.prompt("Paste your GitHub token", hide_input=True)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Login cancelled.[/]")
            raise typer.Exit(0)

    token = (token or "").strip()
    if not token:
        console.print("[red]✗[/] Empty token. Nothing stored.")
        raise typer.Exit(1)

    if not _looks_like_token(token):
        console.print(
            "[yellow]⚠[/] Token format looks unusual. "
            "Continuing anyway — GitHub will validate it."
        )

    # Store first (so we can clean up on failure if we want)
    try:
        backend = set_token(token)
    except AuthenticationError as exc:
        console.print(f"[red]✗[/] Could not store token: {exc}")
        raise typer.Exit(1)

    # Validate against GitHub
    console.print("[dim]Validating token with GitHub…[/]")

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
        # Don't leave a bad token stored if validation fails hard on auth
        if getattr(exc, "status_code", None) in (401, 403):
            delete_token()
            console.print(
                Panel(
                    f"[red]Authentication failed[/]\n\n{exc}\n\n"
                    "[dim]Token was not saved. Check scopes and expiration.[/]",
                    border_style="red",
                    title="✗ Login failed",
                )
            )
            raise typer.Exit(1)
        console.print(f"[yellow]⚠[/] Token stored but API check had an issue: {exc}")
        console.print(f"[green]✓[/] Token saved via [bold]{backend}[/]")
        raise typer.Exit(0)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]⚠[/] Network/validation error: {exc}")
        console.print(
            f"[green]✓[/] Token was still saved via [bold]{backend}[/]. "
            "Run [cyan]ab-hub auth status[/] later to confirm."
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
                f"[bold green]✓ Logged in successfully[/]\n\n"
                f"[bold]User[/]      {login_name}"
                + (f"  ([dim]{name}[/])" if name else "")
                + f"\n[bold]Storage[/]   {backend}\n"
                f"[bold]API rate[/]  {remaining}/{limit} remaining"
            ),
            border_style="green",
            title="Welcome",
            padding=(1, 2),
        )
    )
    console.print()
    console.print("[dim]Next:[/]  [cyan]ab-hub scan[/]  — discover your repositories")
    console.print()


@app.command("status")
def status() -> None:
    """Show current authentication status and rate limits."""
    token = get_token()
    source = token_source()

    if not token:
        console.print()
        console.print(
            Panel(
                Text.from_markup(
                    "[yellow]Not authenticated[/]\n\n"
                    "Run [bold cyan]ab-hub auth login[/] to connect your GitHub account.\n"
                    "Or set [bold]GITHUB_TOKEN[/] in the environment."
                ),
                border_style="yellow",
                title="Status",
                padding=(1, 2),
            )
        )
        console.print()
        raise typer.Exit(1)

    console.print("[dim]Checking GitHub connection…[/]")

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
                    f"[red]Token found but API check failed[/]\n\n"
                    f"{exc}\n\n"
                    f"[dim]Source: {source}[/]\n"
                    "Try [cyan]ab-hub auth logout[/] then [cyan]ab-hub auth login[/]."
                ),
                border_style="red",
                title="✗ Status",
                padding=(1, 2),
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
    table.add_row("User", f"[cyan]{user.get('login')}[/]")
    if user.get("name"):
        table.add_row("Name", str(user.get("name")))
    table.add_row("Token source", source)
    table.add_row("Core rate", f"{core.get('remaining', '?')} / {core.get('limit', '?')}")
    table.add_row("Search rate", f"{search.get('remaining', '?')} / {search.get('limit', '?')}")
    if user.get("html_url"):
        table.add_row("Profile", user["html_url"])

    console.print()
    console.print(
        Panel(table, title="[green]✓ Connected[/]", border_style="green", padding=(1, 1))
    )
    console.print()


@app.command("logout")
def logout() -> None:
    """Remove stored credentials."""
    had = get_token() is not None
    delete_token()
    console.print()
    if had:
        console.print(
            Panel(
                "[green]✓[/] Logged out. Credentials removed from keyring and local config.",
                border_style="green",
                padding=(0, 2),
            )
        )
    else:
        console.print(
            Panel(
                "[dim]No stored credentials found. Already logged out.[/]",
                border_style="dim",
                padding=(0, 2),
            )
        )
    console.print()
