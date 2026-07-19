from __future__ import annotations
import json, re
from pathlib import Path
from agents.base import BaseAgent
from core.types import FixAction, ProjectKind

class FixerAgent(BaseAgent):
    name = "fixer"
    def __init__(self, memory, guard=None, knowledge_path=None):
        super().__init__(memory, guard)
        self.knowledge_path = Path(knowledge_path or Path(__file__).resolve().parent.parent / "knowledge" / "known_errors.json")
        try: self.rules = (json.loads(self.knowledge_path.read_text(encoding="utf-8"))).get("rules") or []
        except Exception: self.rules = []
    def match(self, log_text, kind: ProjectKind):
        text = log_text or ""
        for lesson in self.memory.find_lessons(text, stack=kind.value):
            return FixAction(rule_id=f"memory:{lesson.get('id')}", action=lesson.get("fix_action") or "unknown",
                            params=lesson.get("fix_params") or {}, description=f"memory hits={lesson.get('hits')}")
        for rule in self.rules:
            stacks = rule.get("stacks") or []
            if stacks and kind.value not in stacks and kind != ProjectKind.UNKNOWN: continue
            for pat in rule.get("patterns") or []:
                m = re.search(pat, text, re.I | re.M)
                if m:
                    fix = dict(rule.get("fix") or {}); action = fix.pop("action", "unknown"); params = dict(fix)
                    if "args_from_match" in params:
                        params.pop("args_from_match", None)
                        if m.groups(): params["package"] = m.group(1)
                    return FixAction(rule_id=rule.get("id", "rule"), action=action, params=params, description=rule.get("description", ""))
        return None
    def apply(self, action: FixAction, project_dir, kind: ProjectKind):
        self.log(f"fix {action.rule_id}: {action.action}")
        cwd = Path(project_dir); a = action.action; p = action.params or {}
        if a == "pip_install":
            pkg = p.get("package") or p.get("packages")
            if not pkg: return False, "no package"
            vpy = cwd / ".venv" / "Scripts" / "python.exe"; py = str(vpy) if vpy.exists() else "python"
            code, out = self.run_cmd([py, "-m", "pip", "install", str(pkg)], cwd=cwd); ok = code == 0
            self.memory.record_lesson(out[-500:], a, p, kind.value, ok); return ok, out
        if a == "npm_install":
            code, out = self.run_cmd(["npm", "install"], cwd=cwd); ok = code == 0
            self.memory.record_lesson(out[-500:], a, p, kind.value, ok); return ok, out
        if a == "npm_install_dev":
            pkg = p.get("package", ""); cmd = ["npm", "install", "--save-dev", pkg] if pkg else ["npm", "install"]
            code, out = self.run_cmd(cmd, cwd=cwd); ok = code == 0
            self.memory.record_lesson(out[-500:], a, p, kind.value, ok); return ok, out
        if a == "defender_exclusion":
            ps = "Add-MpPreference -ExclusionPath '%s'" % str(cwd)
            code, out = self.run_cmd(["powershell", "-NoProfile", "-Command", ps], cwd=cwd); ok = code == 0
            self.memory.record_lesson("Access is denied", a, {"path": str(cwd)}, kind.value, ok); return ok, out
        if a == "report_toolchain":
            msg = "Нужен toolchain: %s" % p.get("tool", "?"); return False, msg
        if a == "llm_or_manual":
            return False, p.get("hint") or "LLM/manual needed"
        return False, "unknown action %s" % a
