from __future__ import annotations
from pathlib import Path
import json
from agents.base import BaseAgent

class ElectronBuilder(BaseAgent):
    name = "builder.electron"
    def prepare(self, project_dir, entrypoint=None):
        root = Path(project_dir)
        code, out = self.run_cmd(["npm", "install"], cwd=root, timeout=7200)
        if code != 0: return False, out
        try: pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
        except Exception: pkg = {}
        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        if "electron-builder" not in deps:
            code2, out2 = self.run_cmd(["npm", "install", "--save-dev", "electron-builder"], cwd=root, timeout=3600)
            out += "\n" + out2
            if code2 != 0: return False, out
        return True, out
    def build(self, project_dir, entrypoint=None, onefile=True):
        root = Path(project_dir)
        try: pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
        except Exception: pkg = {}
        scripts = pkg.get("scripts") or {}
        if "dist" in scripts: cmd = ["npm", "run", "dist"]
        elif "build" in scripts: cmd = ["npm", "run", "build"]
        else: cmd = ["npx", "electron-builder", "--win"]
        code, out = self.run_cmd(cmd, cwd=root, timeout=10800)
        artifacts = []
        for folder in ("dist", "release", "out"):
            d = root / folder
            if d.exists():
                artifacts += [str(p) for p in d.rglob("*") if p.is_file() and p.suffix.lower() in {".exe", ".msi", ".appx"}]
        return code == 0 and bool(artifacts), out, artifacts
