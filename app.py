#!/usr/bin/env python3
"""BuildForge Agents — NEURAL_ARCHITECT_PREMIUM++ entrypoint."""
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import typer
from rich import print as rprint
from core.orchestrator import Orchestrator
from core.types import Mode
from llm.router import make_llm
from neural_core import KERNEL_NAME, KERNEL_VERSION, AUTHOR, CONTACTS

cli = typer.Typer(add_completion=False, help=f"{KERNEL_NAME} v{KERNEL_VERSION}")

@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    project: str = typer.Option(None, "--project", "-p"),
    mode: str = typer.Option("autopilot", "--mode", "-m"),
    llm: str = typer.Option("none", "--llm"),
    model: str = typer.Option(None, "--model"),
    target: str = typer.Option("exe+installer", "--target", "-t"),
    entrypoint: str = typer.Option(None, "--entry"),
    gguf: str = typer.Option(None, "--gguf"),
    serve_phone: bool = typer.Option(False, "--serve-phone"),
    port: int = typer.Option(8787, "--port"),
    gui: bool = typer.Option(False, "--gui"),
):
    rprint(f"[bold cyan]{KERNEL_NAME}[/] v{KERNEL_VERSION}")
    rprint(f"[dim]{AUTHOR} · {CONTACTS.get('telegram')} · {CONTACTS.get('vk')}[/]")
    if ctx.invoked_subcommand is not None:
        return
    orch = Orchestrator(max_fix_retries=int(os.getenv("BUILDFORGE_MAX_FIX_RETRIES", "3")))
    orch.set_llm(make_llm(llm, model=model, model_path=gguf))
    if gui or (not project and not serve_phone):
        try:
            from ui.main_window import run_ui
            run_ui(); return
        except Exception as e:
            rprint(f"[yellow]GUI unavailable ({e}), CLI mode[/]")
    if serve_phone:
        from server.phone_api import run_phone_server
        rprint(f"[green]Phone API on 0.0.0.0:{port}[/]")
        run_phone_server(orch, port=port); return
    if not project:
        rprint("[red]Укажи --project PATH или --gui / --serve-phone[/]"); raise typer.Exit(2)
    m = Mode(mode) if mode in Mode._value2member_map_ else Mode.AUTOPILOT
    res = orch.run(project, mode=m, target=target, entrypoint=entrypoint)
    rprint(res.to_dict())
    raise typer.Exit(0 if res.ok else 1)

if __name__ == "__main__":
    cli()
