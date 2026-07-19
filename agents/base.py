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
        self.memory = memory; self.guard = guard or ResourceGuard()
    def log(self, msg: str, level: str = "info") -> None:
        BUS.emit("log", {"agent": self.name, "level": level, "message": msg})
        self.memory.add_action(self.name, msg, ok=(level != "error"))
    def run_cmd(self, cmd, cwd=None, env=None, timeout: int | None = 3600):
        self.guard.breath()
        if isinstance(cmd, str): shell, args, shown = True, cmd, cmd
        else: shell, args, shown = False, cmd, " ".join(shlex.quote(c) for c in cmd)
        self.log(f"$ {shown}")
        merged = os.environ.copy()
        if env: merged.update(env)
        try:
            p = subprocess.run(args, cwd=str(cwd) if cwd else None, env=merged, shell=shell,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
            if p.returncode != 0: self.log(out[-1500:], level="error")
            elif out.strip(): self.log(out[-800:])
            return p.returncode, out
        except subprocess.TimeoutExpired:
            msg = f"timeout after {timeout}s: {shown}"; self.log(msg, level="error"); return 124, msg
        except Exception as e:
            self.log(str(e), level="error"); return 1, str(e)
    def which(self, name: str) -> Optional[str]:
        from shutil import which; return which(name)
