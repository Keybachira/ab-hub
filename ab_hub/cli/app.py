"""Main Typer application — polished entrypoint."""

from __future__ import annotations

import typer
from rich.console import Console

from ab_hub import __version__
from ab_hub.cli.commands import auth, inspect, report, scan, security
from ab_hub.cli.commands import list as list_cmd
from ab_hub.cli.ui.banner import print_banner, print_home
from ab_hub.github.authentication import get_token

console = Console()

app = typer.Typer(
    name="ab-hub",
    help=(
        "[bold]AB-hub[/] — Project Intelligence & Repository Control System\n\n"
        "Discover, analyze and monitor all your GitHub repositories from the terminal."
    ),
    no_args_is_help=False,  # we show a custom home screen
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=True,
)

# Sub-apps
app.add_typer(auth.app, name="auth", help="Login, status & logout")
app.add_typer(scan.app, name="scan", help="Discover and analyze repositories")
app.add_typer(list_cmd.app, name="list", help="List & filter repositories")
app.add_typer(inspect.app, name="inspect", help="Inspect a specific project")
app.add_typer(security.app, name="security", help="Vulnerability & security monitoring")
app.add_typer(report.app, name="report", help="Reports and exports")

# Top-level convenience aliases
app.command("activity", help="Activity scores overview")(inspect.activity_cmd)
app.command("abandoned", help="Possibly abandoned / dormant projects")(inspect.abandoned_cmd)
app.command("compare", help="Compare two repositories")(inspect.compare_cmd)
app.command("technologies", help="Technology overview across projects")(inspect.technologies_cmd)
app.command("export", help="Export data (json / csv / markdown)")(report.export_cmd)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit"),
    banner: bool = typer.Option(False, "--banner", help="Show banner only"),
) -> None:
    """AB-hub CLI entrypoint."""
    if version:
        console.print(f"[bold cyan]AB-hub[/] v{__version__}")
        raise typer.Exit()

    if banner:
        print_banner(console)
        raise typer.Exit()

    # No subcommand → friendly home screen
    if ctx.invoked_subcommand is None:
        account = None
        connected = False
        token = get_token()
        if token:
            # Best-effort lightweight identity (avoid full network if possible)
            # We only show "connected" if a token exists; status command does full check
            connected = True
            try:
                import asyncio

                from ab_hub.github.client import GitHubClient

                async def _who() -> str | None:
                    async with GitHubClient() as client:
                        user = await client.get_authenticated_user()
                        return user.get("login")

                account = asyncio.run(_who())
            except Exception:
                account = "…"
                connected = True  # token present, even if offline

        print_home(console, account=account, connected=connected)
        raise typer.Exit()
