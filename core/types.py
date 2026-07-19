from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional
import time

class ProjectKind(str, Enum):
    PYTHON = "python"; ELECTRON = "electron"; CSHARP = "csharp"; CPP = "cpp"; HTML = "html"; UNKNOWN = "unknown"

class Mode(str, Enum):
    AUTOPILOT = "autopilot"; MANUAL = "manual"; NEURAL = "neural"

class Stage(str, Enum):
    IDLE = "idle"; DETECT = "detect"; DIAGNOSE = "diagnose"; PREPARE = "prepare"
    BUILD = "build"; FIX = "fix"; PACKAGE = "package"; VERIFY = "verify"; DONE = "done"; FAILED = "failed"

class LlmBackend(str, Enum):
    NONE = "none"; OLLAMA = "ollama"; GGUF = "gguf"; OPENAI = "openai"

@dataclass
class DetectResult:
    kind: ProjectKind
    entrypoint: Optional[str] = None
    confidence: float = 0.0
    hints: dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolReport:
    name: str; ok: bool; detail: str = ""; path: Optional[str] = None

@dataclass
class DiagnoseResult:
    ok: bool
    tools: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    blockers: list = field(default_factory=list)

@dataclass
class FixAction:
    rule_id: str; action: str
    params: dict = field(default_factory=dict)
    description: str = ""

@dataclass
class BuildResult:
    ok: bool; stage: Stage; message: str = ""
    artifacts: list = field(default_factory=list)
    log_tail: str = ""; duration_sec: float = 0.0
    kind: ProjectKind = ProjectKind.UNKNOWN
    meta: dict = field(default_factory=dict)
    def to_dict(self):
        d = asdict(self); d["stage"] = self.stage.value; d["kind"] = self.kind.value; return d

@dataclass
class JobState:
    project_dir: str
    mode: Mode = Mode.AUTOPILOT
    stage: Stage = Stage.IDLE
    kind: ProjectKind = ProjectKind.UNKNOWN
    message: str = ""; progress: float = 0.0
    started_at: float = field(default_factory=time.time)
    artifacts: list = field(default_factory=list)
    last_error: str = ""
    def to_dict(self):
        return {"project_dir": self.project_dir, "mode": self.mode.value, "stage": self.stage.value,
                "kind": self.kind.value, "message": self.message, "progress": self.progress,
                "started_at": self.started_at, "artifacts": self.artifacts, "last_error": self.last_error,
                "elapsed_sec": round(time.time() - self.started_at, 1)}
