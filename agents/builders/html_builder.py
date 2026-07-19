from __future__ import annotations
from pathlib import Path
import zipfile, shutil
from agents.base import BaseAgent

class HtmlBuilder(BaseAgent):
    name = "builder.html"
    def prepare(self, project_dir, entrypoint=None):
        root = Path(project_dir)
        if (root / "package.json").exists() and self.which("npm"):
            code, out = self.run_cmd(["npm", "install"], cwd=root, timeout=3600)
            return code == 0, out
        return True, "ok"
    def build(self, project_dir, entrypoint=None, onefile=True):
        root = Path(project_dir); entry = entrypoint or "index.html"
        if not (root / entry).exists(): return False, "missing " + entry, []
        dist = root / "dist" / "html_app"
        if dist.exists(): shutil.rmtree(dist, ignore_errors=True)
        dist.mkdir(parents=True)
        skip = {".git", "node_modules", "dist", ".venv", "build"}
        for p in root.rglob("*"):
            if any(part in skip for part in p.parts): continue
            if p.is_file():
                dest = dist / p.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dest)
        bat_lines = ["@echo off", "set ENTRY=%~dp0" + entry,
                     'where msedge >nul 2>nul && start "" msedge --app="%ENTRY%" && exit /b 0',
                     'where chrome >nul 2>nul && start "" chrome --app="%ENTRY%" && exit /b 0',
                     'start "" "%ENTRY%"']
        launcher = dist / "run.bat"
        launcher.write_text("\r\n".join(bat_lines) + "\r\n", encoding="utf-8")
        zip_path = root / "dist" / "html_app_portable.zip"
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in dist.rglob("*"):
                if p.is_file(): z.write(p, p.relative_to(dist.parent))
        return True, "packed " + str(zip_path), [str(zip_path), str(launcher)]
