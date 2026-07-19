from __future__ import annotations
from pathlib import Path
from llm.base import LlmClient

class GgufLocalClient(LlmClient):
    name = "gguf"
    def __init__(self, model_path: str | None = None, n_ctx: int = 4096):
        self.model_path = model_path; self.n_ctx = n_ctx; self._llm = None
    def available(self) -> bool:
        try:
            import llama_cpp  # noqa
            return True
        except Exception:
            return False
    def set_model(self, path: str) -> None:
        self.model_path = path; self._llm = None
    def _ensure(self):
        if self._llm is not None: return
        if not self.model_path or not Path(self.model_path).exists():
            raise RuntimeError("GGUF model path not set")
        from llama_cpp import Llama
        self._llm = Llama(model_path=self.model_path, n_ctx=self.n_ctx, verbose=False)
    def is_alive(self) -> bool:
        return bool(self.model_path and Path(self.model_path).exists() and self.available())
    def chat(self, messages: list, stream: bool = False) -> str:
        self._ensure()
        parts = [f"{m.get('role','user').upper()}: {m.get('content','')}" for m in messages]
        parts.append("ASSISTANT:")
        out = self._llm("\n".join(parts), max_tokens=1024, stop=["USER:", "SYSTEM:"], echo=False)
        return (out.get("choices") or [{}])[0].get("text", "").strip()
