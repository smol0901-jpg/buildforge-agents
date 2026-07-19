from __future__ import annotations
from pathlib import Path
import shutil
from agents.base import BaseAgent

class CppBuilder(BaseAgent):
    name = "builder.cpp"
    def prepare(self, project_dir, entrypoint=None):
        root = Path(project_dir); bdir = root / "build"; bdir.mkdir(exist_ok=True)
        if shutil.which("cl"): cmd = ["cmake", "-S", str(root), "-B", str(bdir)]
        else: cmd = ["cmake", "-S", str(root), "-B", str(bdir), "-G", "MinGW Makefiles"]
        code, out = self.run_cmd(cmd, cwd=root, timeout=3600)
        return code == 0, out
    def build(self, project_dir, entrypoint=None, onefile=True):
        root = Path(project_dir); bdir = root / "build"
        code, out = self.run_cmd(["cmake", "--build", str(bdir), "--config", "Release"], cwd=root, timeout=7200)
        artifacts = [str(p) for p in bdir.rglob("*.exe")]
        if artifacts:
            dist = root / "dist"; dist.mkdir(exist_ok=True)
            for a in list(artifacts):
                try:
                    dest = dist / Path(a).name; shutil.copy2(a, dest); artifacts.append(str(dest))
                except Exception: pass
        return code == 0 and bool(artifacts), out, list(dict.fromkeys(artifacts))
