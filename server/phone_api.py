from __future__ import annotations
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from core.event_bus import BUS
from core.types import Mode
from core.machine_profile import profile_summary

app = FastAPI(title="BuildForge Phone API", version="1.1")
_orch = None
_clients: list = []


class BuildReq(BaseModel):
    project_dir: str
    mode: str = "neural"
    target: str = "exe+installer"
    entrypoint: Optional[str] = None


def attach_orchestrator(orch) -> None:
    global _orch
    _orch = orch

    def _broadcast(data: dict):
        for ws in list(_clients):
            try:
                asyncio.get_event_loop().create_task(ws.send_json(data))
            except Exception:
                if ws in _clients:
                    _clients.remove(ws)

    BUS.on("*", lambda d: _broadcast(d))


@app.get("/")
def index():
    html = """<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1">
<title>BuildForge Phone</title>
<style>body{font-family:system-ui;background:#0d1117;color:#e6edf3;margin:16px}
button{background:#1f6feb;color:#fff;border:0;padding:12px 16px;border-radius:8px;font-size:16px;width:100%;margin:6px 0}
pre{background:#161b22;padding:12px;border-radius:8px;max-height:45vh;overflow:auto;white-space:pre-wrap}
input,select{width:100%;padding:10px;border-radius:8px;border:1px solid #30363d;background:#0d1117;color:#e6edf3;box-sizing:border-box;margin:4px 0}
.g{font-size:13px;color:#8b9bb0;margin:8px 0}</style></head>
<body><h2>⚒️ BuildForge · NAP++</h2>
<p id=st class=g>…</p>
<p id=guard class=g>guard: …</p>
<input id=proj placeholder="D:\\MyApp">
<select id=mode><option value=neural>neural</option><option value=autopilot>autopilot</option><option value=manual>manual</option></select>
<button onclick=build()>▶ Start</button>
<button onclick=stop()>⏹ Stop</button>
<pre id=log></pre>
<script>
const log=document.getElementById('log'); const st=document.getElementById('st'); const gd=document.getElementById('guard');
const ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');
ws.onmessage=(e)=>{const d=JSON.parse(e.data);
  if(d.event==='log') log.textContent+=(d.message||'')+'\\n';
  if(d.event==='status'){ st.textContent=JSON.stringify({stage:d.stage,message:d.message,progress:d.progress}); if(d.guard) gd.textContent='guard '+JSON.stringify(d.guard); }
  if(d.event==='guard') gd.textContent='guard '+JSON.stringify(d);
};
async function refresh(){const j=await (await fetch('/api/status')).json(); st.textContent=JSON.stringify({stage:j.stage,message:j.message}); gd.textContent='guard '+JSON.stringify(j.guard||j.ram); }
async function build(){const project_dir=document.getElementById('proj').value; const mode=document.getElementById('mode').value;
  await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_dir,mode})});}
async function stop(){await fetch('/api/stop',{method:'POST'})}
refresh(); setInterval(refresh,2500);
</script></body></html>"""
    return HTMLResponse(html)


@app.get("/api/status")
def status():
    if not _orch:
        return {"ok": False}
    st = _orch.state.to_dict() if _orch.state else {"stage": "idle"}
    st["guard"] = _orch.guard.status_dict()
    st["memory"] = _orch.memory.stats()
    st["kernel"] = _orch.memory.get_fact("kernel")
    st["profile"] = profile_summary()
    return st


@app.get("/api/logs")
def logs(tail: int = 100):
    return {"logs": [h for h in BUS.history if h.get("event") == "log"][-tail:]}


@app.post("/api/build")
def build(req: BuildReq):
    if not _orch:
        return JSONResponse({"ok": False}, status_code=500)
    import threading

    mode = Mode(req.mode) if req.mode in Mode._value2member_map_ else Mode.NEURAL
    threading.Thread(
        target=lambda: _orch.run(req.project_dir, mode=mode, target=req.target, entrypoint=req.entrypoint),
        daemon=True,
    ).start()
    return {"ok": True, "started": True}


@app.post("/api/stop")
def stop():
    if _orch:
        _orch.stop()
    return {"ok": True}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    _clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in _clients:
            _clients.remove(ws)


def run_phone_server(orch, host: str = "0.0.0.0", port: int = 8787):
    import uvicorn

    attach_orchestrator(orch)
    uvicorn.run(app, host=host, port=port, log_level="info")
