#!/usr/bin/env python3
"""BuildForge Agents — NEURAL_ARCHITECT_PREMIUM++ entrypoint."""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import typer
from rich import print as rprint

from core.machine_profile import apply_env_defaults, profile_summary, DEFAULT_MODE, DEFAULT_LLM, DEFAULT_OLLAMA_MODEL
from core.orchestrator import Orchestrator
from core.types import Mode
from llm.router import make_llm
from neural_core import KERNEL_NAME, KERNEL_VERSION, AUTHOR, CONTACTS

# Apply owner-machine defaults before CLI parses (env can still override)
apply_env_defaults()

cli = typer.Typer(add_completion=False, help=f"{KERNEL_NAME} v{KERNEL_VERSION}")


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    project: str = typer.Option(None, "--project", "-p"),
    mode: str = typer.Option(None, "--mode", "-m", help="autopilot|manual|neural (default from profile)"),
    llm: str = typer.Option(None, "--llm", help="none|ollama|openai|gguf"),
    model: str = typer.Option(None, "--model"),
    target: str = typer.Option("exe+installer", "--target", "-t"),
    entrypoint: str = typer.Option(None, "--entry"),
    gguf: str = typer.Option(None, "--gguf"),
    serve_phone: bool = typer.Option(False, "--serve-phone"),
    port: int = typer.Option(None, "--port"),
    gui: bool = typer.Option(False, "--gui"),
    profile: bool = typer.Option(False, "--profile", help="Show machine profile and exit"),
):
    rprint(f"[bold cyan]{KERNEL_NAME}[/] v{KERNEL_VERSION}")
    rprint(f"[dim]{AUTHOR} · {CONTACTS.get('telegram')} · {CONTACTS.get('vk')}[/]")
    rprint(
        f"[dim]anti-freeze: CPU≥{os.getenv('BUILDFORGE_CPU_CRITICAL')}% · "
        f"RAM≥{os.getenv('BUILDFORGE_RAM_CRITICAL')}% → gentle paced[/]"
    )

    if profile:
        rprint(profile_summary())
        raise typer.Exit(0)

    if ctx.invoked_subcommand is not None:
        return

    mode_s = mode or os.getenv("BUILDFORGE_MODE", DEFAULT_MODE)
    llm_s = llm or os.getenv("BUILDFORGE_LLM", DEFAULT_LLM)
    model_s = model or os.getenv("BUILDFORGE_MODEL", DEFAULT_OLLAMA_MODEL)
    port_i = port if port is not None else int(os.getenv("BUILDFORGE_PHONE_PORT", "8787"))

    orch = Orchestrator(max_fix_retries=int(os.getenv("BUILDFORGE_MAX_FIX_RETRIES", "2")))
    try:
        orch.set_llm(make_llm(llm_s, model=model_s, model_path=gguf))
    except Exception as e:
        rprint(f"[yellow]LLM init: {e} · continue without LLM[/]")
        orch.set_llm(None)

    if gui or (not project and not serve_phone):
        try:
            from ui.main_window import run_ui

            run_ui()
            return
        except Exception as e:
            rprint(f"[yellow]GUI unavailable ({e}), CLI mode[/]")

    if serve_phone:
        from server.phone_api import run_phone_server

        rprint(f"[green]Phone API on 0.0.0.0:{port_i}[/]")
        run_phone_server(orch, port=port_i)
        return

    if not project:
        rprint("[red]Укажи --project PATH или --gui / --serve-phone / --profile[/]")
        raise typer.Exit(2)

    m = Mode(mode_s) if mode_s in Mode._value2member_map_ else Mode.AUTOPILOT
    res = orch.run(project, mode=m, target=target, entrypoint=entrypoint)
    rprint(res.to_dict())
    raise typer.Exit(0 if res.ok else 1)


if __name__ == "__main__":
    cli()
