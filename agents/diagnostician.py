from __future__ import annotations
import sys, shutil
from agents.base import BaseAgent
from core.types import DiagnoseResult, ProjectKind, ToolReport

class DiagnosticianAgent(BaseAgent):
    name = "diagnostician"
    def diagnose(self, project_dir, kind: ProjectKind):
        tools, warnings, blockers = [], [], []
        def check(name, bin_name=None, required=False):
            path = shutil.which(bin_name or name); ok = path is not None
            tools.append(ToolReport(name=name, ok=ok, path=path, detail="found" if ok else "missing"))
            if not ok and required: blockers.append(f"Не найден toolchain: {name}")
            elif not ok: warnings.append(f"Опционально отсутствует: {name}")
        check("git")
        tools.append(ToolReport(name="python", ok=True, path=sys.executable, detail=sys.version.split()[0]))
        if kind == ProjectKind.PYTHON:
            check("pyinstaller")
            if not shutil.which("pyinstaller"): warnings.append("PyInstaller поставим в venv")
        elif kind == ProjectKind.ELECTRON:
            check("node", required=True); check("npm", required=True)
        elif kind == ProjectKind.CSHARP:
            check("dotnet", required=True)
        elif kind == ProjectKind.CPP:
            check("cmake", required=True)
            if not (shutil.which("cl") or shutil.which("g++") or shutil.which("clang++")):
                blockers.append("Нет C++ компилятора"); tools.append(ToolReport(name="cxx_compiler", ok=False, detail="missing"))
            else: tools.append(ToolReport(name="cxx_compiler", ok=True, detail="found"))
        elif kind == ProjectKind.HTML:
            check("node"); check("npm")
        check("makensis"); check("iscc")
        ok = len(blockers) == 0
        self.log(f"diagnose {kind.value} ok={ok}")
        return DiagnoseResult(ok=ok, tools=tools, warnings=warnings, blockers=blockers)
