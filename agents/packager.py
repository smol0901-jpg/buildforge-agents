from __future__ import annotations
from pathlib import Path
import zipfile
from datetime import datetime
from agents.base import BaseAgent

class PackagerAgent(BaseAgent):
    name = "packager"
    def make_zip(self, artifacts, project_dir, name="app"):
        root = Path(project_dir)
        out = root / "dist" / f"{name}_portable_{datetime.now():%Y%m%d_%H%M%S}.zip"
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for a in artifacts:
                p = Path(a)
                if p.is_file(): z.write(p, p.name)
        self.log("ZIP " + str(out)); return str(out)
    def make_installer(self, payload_exe, project_dir, name="BuildForgeApp"):
        root = Path(project_dir); out_dir = root / "dist" / "installers"; out_dir.mkdir(parents=True, exist_ok=True)
        payload = Path(payload_exe)
        if not payload.exists(): return []
        results = []
        # NSIS minimal
        if self.which("makensis"):
            nsi = out_dir / "installer.nsi"
            content = "\n".join([
                '!Name "%s"' % name,
                'OutFile "%s"' % str(out_dir / (name + "_Setup.exe")).replace("/", "\\"),
                'InstallDir "$PROGRAMFILES\\%s"' % name,
                "Page directory", "Page instfiles", 'Section "Install"',
                '  SetOutPath "$INSTDIR"',
                '  File "%s"' % str(payload).replace("/", "\\"),
                '  CreateShortCut "$DESKTOP\\%s.lnk" "$INSTDIR\\%s"' % (name, payload.name),
                "SectionEnd",
            ])
            nsi.write_text(content, encoding="utf-8")
            code, out = self.run_cmd(["makensis", str(nsi)], cwd=out_dir)
            setup = out_dir / (name + "_Setup.exe")
            if code == 0 and setup.exists(): results.append(str(setup))
        if not results: self.log("NSIS/Inno not found — ZIP only")
        return results
