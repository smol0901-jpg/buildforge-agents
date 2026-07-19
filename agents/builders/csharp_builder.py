from __future__ import annotations
from pathlib import Path
from agents.base import BaseAgent

class CsharpBuilder(BaseAgent):
    name = "builder.csharp"
    def prepare(self, project_dir, entrypoint=None):
        cmd = ["dotnet", "restore"] + ([entrypoint] if entrypoint else [])
        code, out = self.run_cmd(cmd, cwd=project_dir, timeout=3600)
        return code == 0, out
    def build(self, project_dir, entrypoint=None, onefile=True):
        root = Path(project_dir); proj = entrypoint
        if not proj:
            cs = list(root.glob("*.csproj")) or list(root.rglob("*.csproj"))
            proj = str(cs[0]) if cs else None
        if not proj: return False, "no .csproj", []
        out_dir = root / "dist_publish"
        cmd = ["dotnet", "publish", proj, "-c", "Release", "-r", "win-x64",
               "--self-contained", "true", "-p:PublishSingleFile=true", "-o", str(out_dir)]
        code, out = self.run_cmd(cmd, cwd=root, timeout=7200)
        artifacts = [str(p) for p in out_dir.rglob("*.exe")] if out_dir.exists() else []
        return code == 0 and bool(artifacts), out, artifacts
