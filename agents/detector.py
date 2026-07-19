from __future__ import annotations
from pathlib import Path
import json
from agents.base import BaseAgent
from core.types import DetectResult, ProjectKind

class DetectorAgent(BaseAgent):
    name = "detector"
    def detect(self, project_dir):
        root = Path(project_dir)
        if not root.is_dir():
            return DetectResult(ProjectKind.UNKNOWN, confidence=0.0, hints={"error": "not a directory"})
        names = {p.name.lower() for p in root.iterdir()}
        hints = {"files": sorted(list(names))[:80]}
        if "package.json" in names:
            try: pkg = json.loads((root / "package.json").read_text(encoding="utf-8", errors="replace"))
            except Exception: pkg = {}
            deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
            scripts = pkg.get("scripts") or {}
            if "electron" in deps or "electron-builder" in deps or any("electron" in str(v) for v in scripts.values()):
                main = pkg.get("main") or "main.js"
                self.log(f"Electron detected main={main}")
                return DetectResult(ProjectKind.ELECTRON, entrypoint=main, confidence=0.95, hints=hints)
        if list(root.glob("*.csproj")) or list(root.glob("*.sln")):
            csproj = next(iter(list(root.glob("*.csproj")) + list(root.rglob("*.csproj"))), None)
            self.log(f"C# detected {csproj}")
            return DetectResult(ProjectKind.CSHARP, entrypoint=str(csproj) if csproj else None, confidence=0.93, hints=hints)
        if (root / "CMakeLists.txt").exists() or list(root.glob("*.vcxproj")):
            self.log("C++/CMake detected")
            return DetectResult(ProjectKind.CPP, entrypoint=str(root / "CMakeLists.txt"), confidence=0.9, hints=hints)
        py_markers = {"pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"}
        py_files = list(root.glob("*.py"))
        if py_markers & names or py_files:
            entry = None
            for cand in ("main.py", "app.py", "run.py", "__main__.py"):
                if (root / cand).exists(): entry = cand; break
            if not entry and py_files:
                ranked = sorted([p for p in py_files if "test" not in p.name.lower()], key=lambda p: p.stat().st_size, reverse=True)
                entry = ranked[0].name if ranked else py_files[0].name
            self.log(f"Python detected entry={entry}")
            return DetectResult(ProjectKind.PYTHON, entrypoint=entry, confidence=0.92, hints=hints)
        if "index.html" in names or list(root.glob("*.html")):
            entry = "index.html" if (root / "index.html").exists() else next(root.glob("*.html")).name
            self.log(f"HTML detected entry={entry}")
            return DetectResult(ProjectKind.HTML, entrypoint=entry, confidence=0.85, hints=hints)
        self.log("Unknown project", level="error")
        return DetectResult(ProjectKind.UNKNOWN, confidence=0.0, hints=hints)
