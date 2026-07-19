from __future__ import annotations
"""
Anti-freeze / paced load guard for BuildForge Agents.

Hard caps (defaults, overridable via env):
  CPU  >= 97%  → gentle / paced mode
  RAM  >= 96%  → gentle / paced mode

In gentle mode the system:
  - waits until load drops below recover thresholds
  - inserts staged pauses between heavy steps (exponential backoff)
  - lowers subprocess priority on Windows (BELOW_NORMAL)
  - never starts a new heavy command while over hard caps
"""
from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, asdict
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore

from core.event_bus import BUS


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_bool(name: str, default: bool = True) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "no", "off")


@dataclass
class LoadSample:
    cpu: float = 0.0
    ram: float = 0.0
    mode: str = "normal"  # normal | gentle | critical
    gentle: bool = False
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResourceGuard:
    """
    CPU/RAM anti-freeze guard.

    Thresholds (user request):
      cpu_critical = 97.0
      ram_critical = 96.0
    Recover slightly below so we don't thrash the boundary.
    """

    def __init__(
        self,
        cpu_critical: float | None = None,
        ram_critical: float | None = None,
        cpu_recover: float | None = None,
        ram_recover: float | None = None,
        enabled: bool | None = None,
        poll_sec: float | None = None,
        max_wait_sec: float | None = None,
        base_pause_sec: float | None = None,
        max_pause_sec: float | None = None,
    ):
        self.cpu_critical = cpu_critical if cpu_critical is not None else _env_float("BUILDFORGE_CPU_CRITICAL", 97.0)
        self.ram_critical = ram_critical if ram_critical is not None else _env_float("BUILDFORGE_RAM_CRITICAL", 96.0)
        # recover a bit lower to avoid flapping
        self.cpu_recover = cpu_recover if cpu_recover is not None else _env_float("BUILDFORGE_CPU_RECOVER", 90.0)
        self.ram_recover = ram_recover if ram_recover is not None else _env_float("BUILDFORGE_RAM_RECOVER", 90.0)
        self.enabled = enabled if enabled is not None else _env_bool("BUILDFORGE_GUARD_ENABLED", True)
        self.poll_sec = poll_sec if poll_sec is not None else _env_float("BUILDFORGE_GUARD_POLL", 0.75)
        self.max_wait_sec = max_wait_sec if max_wait_sec is not None else _env_float("BUILDFORGE_GUARD_MAX_WAIT", 180.0)
        self.base_pause_sec = base_pause_sec if base_pause_sec is not None else _env_float("BUILDFORGE_GUARD_BASE_PAUSE", 1.0)
        self.max_pause_sec = max_pause_sec if max_pause_sec is not None else _env_float("BUILDFORGE_GUARD_MAX_PAUSE", 12.0)

        self._lock = threading.Lock()
        self._last = LoadSample()
        self._gentle = False
        self._stage_index = 0  # exponential stage counter while gentle
        self._cpu_primed = False
        # lower child process priority when gentle
        self.lower_priority_in_gentle = _env_bool("BUILDFORGE_GUARD_LOW_PRIORITY", True)

        # prime cpu_percent baseline (non-blocking first call returns 0)
        if psutil:
            try:
                psutil.cpu_percent(interval=None)
                self._cpu_primed = True
            except Exception:
                pass

    # ---------- sampling ----------
    def sample(self) -> LoadSample:
        cpu = 0.0
        ram = 0.0
        if psutil:
            try:
                # interval=None → non-blocking after prime
                cpu = float(psutil.cpu_percent(interval=None if self._cpu_primed else 0.15))
                self._cpu_primed = True
            except Exception:
                cpu = 0.0
            try:
                ram = float(psutil.virtual_memory().percent)
            except Exception:
                ram = 0.0

        over = (cpu >= self.cpu_critical) or (ram >= self.ram_critical)
        still_high = (cpu >= self.cpu_recover) or (ram >= self.ram_recover)

        with self._lock:
            if over:
                self._gentle = True
            elif self._gentle and not still_high:
                # recovered under both recover lines
                self._gentle = False
                self._stage_index = 0

            mode = "normal"
            if over:
                mode = "critical"
            elif self._gentle:
                mode = "gentle"

            s = LoadSample(cpu=round(cpu, 1), ram=round(ram, 1), mode=mode, gentle=self._gentle, timestamp=time.time())
            self._last = s
            return s

    @property
    def last(self) -> LoadSample:
        with self._lock:
            return self._last

    @property
    def is_gentle(self) -> bool:
        with self._lock:
            return self._gentle

    def status_dict(self) -> dict[str, Any]:
        s = self.sample()
        return {
            **s.to_dict(),
            "cpu_critical": self.cpu_critical,
            "ram_critical": self.ram_critical,
            "cpu_recover": self.cpu_recover,
            "ram_recover": self.ram_recover,
            "stage_index": self._stage_index,
            "enabled": self.enabled,
        }

    def _emit(self, message: str, level: str = "warn") -> None:
        BUS.emit("log", {"agent": "resource_guard", "level": level, "message": message})
        BUS.emit("guard", self.status_dict())

    # ---------- wait / paced ----------
    def wait_if_critical(self, timeout: float | None = None, reason: str = "") -> LoadSample:
        """Block while CPU>=97 or RAM>=96 until recover or timeout."""
        s = self.sample()
        if not self.enabled or not psutil:
            return s
        if s.cpu < self.cpu_critical and s.ram < self.ram_critical:
            return s

        limit = self.max_wait_sec if timeout is None else timeout
        start = time.time()
        stage = 0
        self._emit(
            f"anti-freeze ON · CPU {s.cpu}% / RAM {s.ram}% "
            f"(caps {self.cpu_critical}/{self.ram_critical}) · gentle paced mode"
            + (f" · {reason}" if reason else "")
        )

        while True:
            s = self.sample()
            if s.cpu < self.cpu_recover and s.ram < self.ram_recover:
                self._emit(
                    f"anti-freeze OFF · recovered CPU {s.cpu}% / RAM {s.ram}% "
                    f"(recover <{self.cpu_recover}/{self.ram_recover})",
                    level="info",
                )
                with self._lock:
                    self._stage_index = 0
                return s

            elapsed = time.time() - start
            if elapsed >= limit:
                self._emit(
                    f"anti-freeze wait timeout {limit:.0f}s · continue carefully "
                    f"CPU {s.cpu}% / RAM {s.ram}%",
                    level="warn",
                )
                return s

            # exponential staged pause: 1, 2, 4, 8 … up to max_pause
            pause = min(self.max_pause_sec, self.base_pause_sec * (2 ** min(stage, 4)))
            stage += 1
            with self._lock:
                self._stage_index = stage
            time.sleep(pause)

    def breath(self, seconds: float | None = None, reason: str = "step") -> LoadSample:
        """
        Call before/after heavy work.
        - If over hard caps → wait_if_critical (staged)
        - If still in gentle → short paced pause (exponential by stage_index)
        """
        s = self.sample()
        if not self.enabled:
            return s

        if s.cpu >= self.cpu_critical or s.ram >= self.ram_critical:
            s = self.wait_if_critical(reason=reason)

        if self.is_gentle:
            with self._lock:
                idx = self._stage_index
                self._stage_index = min(idx + 1, 8)
            pause = seconds if seconds is not None else min(
                self.max_pause_sec,
                self.base_pause_sec * (2 ** min(idx, 3)),
            )
            # minimum gentle pause
            pause = max(pause, 0.4)
            self._emit(
                f"paced breath {pause:.1f}s · stage {idx} · CPU {s.cpu}% RAM {s.ram}% · {reason}",
                level="info",
            )
            time.sleep(pause)
            s = self.sample()
        elif seconds and seconds > 0:
            time.sleep(seconds)
            s = self.sample()
        return s

    def before_command(self, label: str = "") -> dict[str, Any]:
        """Gate before subprocess: wait if critical, return env/priority hints."""
        s = self.breath(reason=f"before:{label}" if label else "before:cmd")
        hints = {
            "gentle": self.is_gentle,
            "load": s.to_dict(),
            "creationflags": 0,
            "preexec": None,
        }
        if self.is_gentle and self.lower_priority_in_gentle:
            # Windows: BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
            if os.name == "nt":
                hints["creationflags"] = 0x00004000
        return hints

    def after_command(self, label: str = "") -> LoadSample:
        return self.breath(reason=f"after:{label}" if label else "after:cmd")

    def stage_pause(self, stage_name: str) -> LoadSample:
        """Explicit pause between pipeline stages (prepare/build/package…)."""
        return self.breath(reason=f"stage:{stage_name}")
