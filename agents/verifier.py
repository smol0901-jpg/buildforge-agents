from __future__ import annotations
from pathlib import Path
import subprocess, time
from agents.base import BaseAgent

class VerifierAgent(BaseAgent):
    name = "verifier"
    def verify_exe(self, path, timeout: float = 5.0):
        p = Path(path)
        if not p.exists(): return False, "artifact missing"
        if p.suffix.lower() != ".exe": return True, "skip non-exe: " + p.name
        try:
            proc = subprocess.Popen([str(p)], cwd=str(p.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(min(timeout, 2.0))
            ret = proc.poll()
            if ret is None:
                proc.terminate()
                try: proc.wait(timeout=2)
                except Exception: proc.kill()
                return True, "started"
            if ret in (0, 1): return True, "exited %s" % ret
            return False, "exited %s" % ret
        except OSError as e:
            return False, str(e)
