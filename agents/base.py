from __future__ import annotations
from abc import ABC
from typing import Optional
import os, subprocess, shlex
from core.event_bus import BUS
from core.resource_guard import ResourceGuard
from core.memory import Memory


class BaseAgent(ABC):
    name = "base"

    def __init__(self, memory: Memory, guard: ResourceGuard | None = None):
        self.memory = memory
        self.guard = guard or ResourceGuard()

    def log(self, msg: str, level: str = "info") -> None:
        BUS.emit("log", {"agent": self.name, "level": level, "message": msg})
        self.memory.add_action(self.name, msg, ok=(level != "error"))

    def run_cmd(self, cmd, cwd=None, env=None, timeout: int | None = 3600):
        if isinstance(cmd, str):
            shell, args, shown = True, cmd, cmd
        else:
            shell, args, shown = False, cmd, " ".join(shlex.quote(c) for c in cmd)

        hints = self.guard.before_command(label=shown[:80])
        self.log(f"$ {shown}" + ("  [gentle]" if hints.get("gentle") else ""))

        merged = os.environ.copy()
        if env:
            merged.update(env)

        # In gentle mode: fewer parallel npm/msbuild threads if user didn't set them
        if hints.get("gentle"):
            merged.setdefault("npm_config_jobs", "1")
            merged.setdefault("CMAKE_BUILD_PARALLEL_LEVEL", "1")
            merged.setdefault("MAX_JOBS", "1")
            # MSBuild single-threaded-ish
            merged.setdefault("CL", "/MP1")

        run_kwargs = dict(
            cwd=str(cwd) if cwd else None,
            env=merged,
            shell=shell,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        cf = hints.get("creationflags") or 0
        if cf and os.name == "nt":
            run_kwargs["creationflags"] = cf

        try:
            p = subprocess.run(args, **run_kwargs)
            out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
            if p.returncode != 0:
                self.log(out[-1500:], level="error")
            elif out.strip():
                self.log(out[-800:])
            self.guard.after_command(label=shown[:80])
            return p.returncode, out
        except subprocess.TimeoutExpired:
            msg = f"timeout after {timeout}s: {shown}"
            self.log(msg, level="error")
            self.guard.after_command(label="timeout")
            return 124, msg
        except Exception as e:
            self.log(str(e), level="error")
            self.guard.after_command(label="error")
            return 1, str(e)

    def which(self, name: str) -> Optional[str]:
        from shutil import which
        return which(name)
