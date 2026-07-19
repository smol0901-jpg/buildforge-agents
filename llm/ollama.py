from __future__ import annotations
import json
import httpx
from llm.base import LlmClient

class OllamaClient(LlmClient):
    name = "ollama"
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url.rstrip("/"); self.model = model
    def is_alive(self) -> bool:
        try:
            return httpx.get(f"{self.base_url}/api/tags", timeout=3.0).status_code == 200
        except Exception:
            return False
    def chat(self, messages: list, stream: bool = False) -> str:
        r = httpx.post(f"{self.base_url}/api/chat", json={"model": self.model, "messages": messages, "stream": False}, timeout=600.0)
        r.raise_for_status(); data = r.json()
        return ((data.get("message") or {}).get("content")) or data.get("response") or ""
