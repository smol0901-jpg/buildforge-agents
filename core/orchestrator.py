from __future__ import annotations
import time, threading
from pathlib import Path
from typing import Optional
from core.types import Mode, Stage, ProjectKind, BuildResult, JobState
from core.memory import Memory
from core.resource_guard import ResourceGuard
from core.event_bus import BUS
from agents.detector import DetectorAgent
from agents.diagnostician import DiagnosticianAgent
from agents.fixer import FixerAgent
from agents.packager import PackagerAgent
from agents.verifier import VerifierAgent
from agents.builders import BUILDERS
from neural_core import system_prompt, KERNEL_NAME, KERNEL_VERSION, AUTHOR, CONTACTS

class Orchestrator:
    """NEURAL_ARCHITECT_PREMIUM++ BuildForge orchestrator."""

    def __init__(self, data_dir=None, max_fix_retries: int = 3):
        data = Path(data_dir or Path.home() / ".buildforge")
        data.mkdir(parents=True, exist_ok=True)
        self.memory = Memory(data / "memory.db")
        self.guard = ResourceGuard()
        self.max_fix_retries = max_fix_retries
        self.detector = DetectorAgent(self.memory, self.guard)
        self.diagnostician = DiagnosticianAgent(self.memory, self.guard)
        self.fixer = FixerAgent(self.memory, self.guard)
        self.packager = PackagerAgent(self.memory, self.guard)
        self.verifier = VerifierAgent(self.memory, self.guard)
        self.state: Optional[JobState] = None
        self._stop = threading.Event()
        self.llm = None
        self.memory.set_fact("kernel", {"name": KERNEL_NAME, "version": KERNEL_VERSION, "author": AUTHOR, "contacts": CONTACTS})

    def set_llm(self, llm_client) -> None:
        self.llm = llm_client

    def stop(self) -> None:
        self._stop.set()
        BUS.emit("status", {"message": "stop requested"})

    def _set(self, stage: Stage, message: str = "", progress: float | None = None):
        if self.state:
            self.state.stage = stage
            self.state.message = message
            if progress is not None:
                self.state.progress = progress
            BUS.emit("status", self.state.to_dict())
        BUS.emit("log", {"agent": "orchestrator", "level": "info", "message": f"[{stage.value}] {message}"})

    def run(self, project_dir: str, mode: Mode = Mode.AUTOPILOT, target: str = "exe+installer", entrypoint: str | None = None) -> BuildResult:
        self._stop.clear()
        t0 = time.time()
        root = str(Path(project_dir).resolve())
        self.state = JobState(project_dir=root, mode=mode)
        self.memory.add_message("system", f"job start mode={mode.value} project={root}")
        BUS.emit("log", {"agent": "orchestrator", "level": "info", "message": f"{KERNEL_NAME} v{KERNEL_VERSION} · mode={mode.value}"})

        self._set(Stage.DETECT, "Определение типа проекта (NAP++ decomposition)", 0.05)
        det = self.detector.detect(root)
        kind = det.kind
        entry = entrypoint or det.entrypoint
        self.state.kind = kind
        if kind == ProjectKind.UNKNOWN:
            self._set(Stage.FAILED, "Не удалось определить тип проекта")
            return BuildResult(False, Stage.FAILED, "unknown project type", kind=kind, duration_sec=time.time()-t0)

        if self._stop.is_set():
            return BuildResult(False, Stage.FAILED, "stopped", kind=kind, duration_sec=time.time()-t0)

        self._set(Stage.DIAGNOSE, f"Диагностика toolchain для {kind.value}", 0.15)
        diag = self.diagnostician.diagnose(root, kind)
        if not diag.ok:
            msg = "; ".join(diag.blockers) or "toolchain blockers"
            if mode == Mode.NEURAL and self.llm:
                advice = self._llm_advice(f"Blockers: {msg}. Project: {root}. Kind: {kind.value}. Fix on Windows?")
                self._set(Stage.FAILED, f"{msg}\nLLM: {advice[:500]}")
            else:
                self._set(Stage.FAILED, msg)
            return BuildResult(False, Stage.FAILED, msg, kind=kind, duration_sec=time.time()-t0, meta={"warnings": diag.warnings})

        builder_cls = BUILDERS.get(kind)
        if not builder_cls:
            return BuildResult(False, Stage.FAILED, "no builder", kind=kind, duration_sec=time.time()-t0)
        builder = builder_cls(self.memory, self.guard)

        self._set(Stage.PREPARE, "Подготовка окружения проекта", 0.3)
        ok, prep_log = builder.prepare(root, entry)
        if not ok:
            if self._fix_loop(prep_log, kind, root, mode):
                ok, prep_log = builder.prepare(root, entry)
        if not ok:
            self._set(Stage.FAILED, "prepare failed")
            return BuildResult(False, Stage.FAILED, prep_log[-2000:], log_tail=prep_log[-2000:], kind=kind, duration_sec=time.time()-t0)

        self._set(Stage.BUILD, f"Сборка {kind.value} → EXE", 0.5)
        ok, blog, artifacts = builder.build(root, entry)
        retries = 0
        while not ok and retries < self.max_fix_retries and not self._stop.is_set():
            retries += 1
            self._set(Stage.FIX, f"Self-healing {retries}/{self.max_fix_retries}", 0.5 + retries * 0.05)
            if not self._fix_loop(blog, kind, root, mode):
                if mode == Mode.NEURAL and self.llm:
                    self._llm_code_fix(root, kind, blog)
                else:
                    break
            ok, blog, artifacts = builder.build(root, entry)

        if not ok or not artifacts:
            self._set(Stage.FAILED, "сборка не дала артефактов (truth chain)")
            self.memory.record_lesson(blog[-800:], "build_failed", {"kind": kind.value}, kind.value, False)
            return BuildResult(False, Stage.FAILED, "build failed", log_tail=blog[-3000:], kind=kind, duration_sec=time.time()-t0)

        self.state.artifacts = list(artifacts)
        final_artifacts = list(artifacts)

        if "installer" in target or "zip" in target or target == "exe+installer":
            self._set(Stage.PACKAGE, "Упаковка ZIP / installer", 0.8)
            name = Path(root).name or "app"
            z = self.packager.make_zip(artifacts, root, name=name)
            if z:
                final_artifacts.append(z)
            exe = next((a for a in artifacts if a.lower().endswith(".exe")), None)
            if exe and "installer" in target:
                final_artifacts += self.packager.make_installer(exe, root, name=name)

        self._set(Stage.VERIFY, "Smoke-проверка (truth verification)", 0.9)
        verify_notes = []
        for a in artifacts:
            vok, vmsg = self.verifier.verify_exe(a)
            verify_notes.append(f"{Path(a).name}: {vmsg}")

        self.memory.record_lesson(f"success {kind.value}", "pipeline_ok", {"entry": entry}, kind.value, True)
        self.memory.add_action("orchestrator", f"done artifacts={len(final_artifacts)}", True)
        self.state.artifacts = final_artifacts
        self._set(Stage.DONE, f"Готово · {len(final_artifacts)} артефакт(ов)", 1.0)
        sig = f"\n— {AUTHOR} · {CONTACTS.get('telegram')} · {KERNEL_NAME}"
        return BuildResult(True, Stage.DONE, "ok" + sig, artifacts=final_artifacts,
                           log_tail="\n".join(verify_notes), duration_sec=time.time()-t0, kind=kind,
                           meta={"kernel": KERNEL_VERSION, "mode": mode.value})

    def _fix_loop(self, log_text: str, kind: ProjectKind, root: str, mode: Mode) -> bool:
        action = self.fixer.match(log_text, kind)
        if not action:
            if mode == Mode.NEURAL and self.llm:
                return self._llm_code_fix(root, kind, log_text)
            return False
        ok, _out = self.fixer.apply(action, root, kind)
        return ok

    def _llm_advice(self, user_msg: str) -> str:
        if not self.llm:
            return ""
        try:
            return self.llm.chat([
                {"role": "system", "content": system_prompt("Ты — ядро BuildForge / NEURAL_ARCHITECT_PREMIUM++. Помогай чинить сборки.")},
                {"role": "user", "content": user_msg},
            ])
        except Exception as e:
            return str(e)

    def _llm_code_fix(self, root: str, kind: ProjectKind, log_text: str) -> bool:
        if not self.llm:
            return False
        prompt = (
            f"Проект: {root}\nСтек: {kind.value}\nЛог ошибки:\n{log_text[-3500:]}\n\n"
            "По DECOMPOSITION + TRUTH CHAIN предложи ОДНУ команду Windows, начинай с CMD: "
        )
        ans = self._llm_advice(prompt)
        BUS.emit("log", {"agent": "llm", "level": "info", "message": (ans or "")[:1000]})
        for line in (ans or "").splitlines():
            if line.strip().upper().startswith("CMD:"):
                cmd = line.split(":", 1)[1].strip()
                code, _out = self.fixer.run_cmd(cmd, cwd=root, timeout=1800)
                self.memory.record_lesson(log_text[-500:], "llm_cmd", {"cmd": cmd}, kind.value, code == 0)
                return code == 0
        return False

    def neural_chat(self, user_text: str, project_dir: str | None = None) -> str:
        self.memory.add_message("user", user_text)
        if not self.llm:
            t = user_text.lower()
            if "собери" in t or "build" in t:
                if not project_dir:
                    return "Укажи папку проекта"
                res = self.run(project_dir, mode=Mode.AUTOPILOT)
                return f"autopilot: ok={res.ok} stage={res.stage.value} artifacts={res.artifacts}"
            return "LLM не подключён. Режим autopilot/manual. Подключи Ollama/GGUF/OpenAI."
        proj = project_dir or (self.state.project_dir if self.state else "")
        ctx = system_prompt(f"project_dir={proj}")
        hist = self.memory.history(20)
        messages = [{"role": "system", "content": ctx}] + hist + [{"role": "user", "content": user_text}]
        ans = self.llm.chat(messages)
        self.memory.add_message("assistant", ans)
        if "ASV_PROD" not in ans and "@ASV_prod" not in ans:
            ans = ans.rstrip() + f"\n\n— {KERNEL_NAME} · {CONTACTS.get('telegram')}"
        return ans
