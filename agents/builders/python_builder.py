from __future__ import annotations
from pathlib import Path
from agents.base import BaseAgent

class PythonBuilder(BaseAgent):
    name = "builder.python"
    def prepare(self, project_dir, entrypoint=None):
        root = Path(project_dir); venv = root / ".venv"; logs = []
        if not venv.exists():
            code, out = self.run_cmd(["python", "-m", "venv", str(venv)], cwd=root); logs.append(out)
            if code != 0: return False, out
        py = str(venv / "Scripts" / "python.exe")
        if not Path(py).exists(): py = str(venv / "bin" / "python")
        code, out = self.run_cmd([py, "-m", "pip", "install", "-U", "pip", "wheel", "pyinstaller"], cwd=root); logs.append(out)
        if (root / "requirements.txt").exists():
            code2, out2 = self.run_cmd([py, "-m", "pip", "install", "-r", "requirements.txt"], cwd=root); logs.append(out2)
            if code2 != 0: return False, "\n".join(logs)
        return code == 0, "\n".join(logs)
    def build(self, project_dir, entrypoint=None, onefile=True):
        root = Path(project_dir); entry = entrypoint or "main.py"
        if not (root / entry).exists(): return False, "entrypoint not found: " + entry, []
        vpy = root / ".venv" / "Scripts" / "python.exe"; py = str(vpy) if vpy.exists() else "python"
        name = Path(entry).stem
        cmd = [py, "-m", "PyInstaller", "--noconfirm", "--clean", "--name", name]
        if onefile: cmd.append("--onefile")
        cmd.append(entry)
        code, out = self.run_cmd(cmd, cwd=root, timeout=7200)
        artifacts = [str(p) for p in (root / "dist").rglob("*.exe")] if (root / "dist").exists() else []
        return code == 0 and bool(artifacts), out, artifacts
