"""Aplicação principal Typer — ponto de entrada polido."""

from __future__ import annotations

import typer
from rich.console import Console

from ab_hub import __version__
from ab_hub.cli.commands import auth, inspect, list as list_cmd, report, scan, security
from ab_hub.cli.ui.banner import print_banner

console = Console()

app = typer.Typer(
    name="ab-hub",
    help=(
        "[bold]AB-hub[/] — Sistema de Inteligência de Projectos e Controlo de Repositórios\n\n"
        "Descubra, analise e monitore todos os seus repositórios GitHub a partir do terminal.\n"
        "Sem argumentos abre o [bold]shell interactivo[/] (sair com [cyan]q[/] + Enter)."
    ),
    no_args_is_help=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=True,
)

# --- Grupos principais (português + aliases inglês) ---
app.add_typer(auth.app, name="autenticacao", help="Entrar, estado e sair da conta")
app.add_typer(auth.app, name="auth", help="[dim]Alias de autenticacao[/]")

app.add_typer(scan.app, name="analisar", help="Descobrir e analisar repositórios")
app.add_typer(scan.app, name="scan", help="[dim]Alias de analisar[/]")

app.add_typer(list_cmd.app, name="listar", help="Listar e filtrar repositórios")
app.add_typer(list_cmd.app, name="list", help="[dim]Alias de listar[/]")

app.add_typer(inspect.app, name="inspeccionar", help="Inspeccionar um projecto específico")
app.add_typer(inspect.app, name="inspect", help="[dim]Alias de inspeccionar[/]")

app.add_typer(security.app, name="seguranca", help="Monitorização de vulnerabilidades e segurança")
app.add_typer(security.app, name="security", help="[dim]Alias de seguranca[/]")

app.add_typer(report.app, name="relatorio", help="Relatórios e exportações")
app.add_typer(report.app, name="report", help="[dim]Alias de relatorio[/]")

# --- Atalhos de nível superior ---
app.command("actividade", help="Visão geral das pontuações de actividade")(inspect.activity_cmd)
app.command("activity", help="[dim]Alias de actividade[/]")(inspect.activity_cmd)

app.command("abandonados", help="Projectos possivelmente abandonados ou dormentes")(
    inspect.abandoned_cmd
)
app.command("abandoned", help="[dim]Alias de abandonados[/]")(inspect.abandoned_cmd)

app.command("comparar", help="Comparar dois repositórios")(inspect.compare_cmd)
app.command("compare", help="[dim]Alias de comparar[/]")(inspect.compare_cmd)

app.command("tecnologias", help="Visão geral de tecnologias nos projectos")(
    inspect.technologies_cmd
)
app.command("technologies", help="[dim]Alias de tecnologias[/]")(inspect.technologies_cmd)

app.command("exportar", help="Exportar dados (json / csv / markdown)")(report.export_cmd)
app.command("export", help="[dim]Alias de exportar[/]")(report.export_cmd)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Mostrar versão e sair"),
    banner: bool = typer.Option(False, "--banner", help="Mostrar apenas o banner"),
    once: bool = typer.Option(
        False,
        "--once",
        help="Não abrir o shell interactivo (modo clássico de um comando)",
    ),
) -> None:
    """Ponto de entrada do CLI AB-hub.

    Sem subcomando abre o shell interactivo. Saia com [cyan]q[/] + Enter.
    """
    if version:
        console.print(f"[bold cyan]AB-hub[/] v{__version__}")
        raise typer.Exit()

    if banner:
        print_banner(console)
        raise typer.Exit()

    # Sem subcomando → shell interactivo (permanece aberto até q)
    if ctx.invoked_subcommand is None and not once:
        from ab_hub.cli.shell import run_interactive_shell

        run_interactive_shell(app)
        raise typer.Exit()
