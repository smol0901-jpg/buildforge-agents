# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
datas = [("neural_core", "neural_core"), ("knowledge", "knowledge"), ("templates", "templates")]
binaries = []
hiddenimports = ["uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto", "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto", "uvicorn.lifespan", "uvicorn.lifespan.on"]
try:
    tmp = collect_all("llama_cpp")
    datas += tmp[0]; binaries += tmp[1]; hiddenimports += tmp[2]
except Exception:
    pass
a = Analysis(["app.py"], pathex=[], binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="BuildForgeAgents", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=True, upx_exclude=[],
          runtime_tmpdir=None, console=True, disable_windowed_traceback=False, argv_emulation=False,
          target_arch=None, codesign_identity=None, entitlements_file=None)
