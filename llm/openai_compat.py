from __future__ import annotations
import os
import httpx
from llm.base import LlmClient

class OpenAICompatClient(LlmClient):
    name = "openai"
    def __init__(self, base_url=None, api_key=None, model: str = "gpt-4o-mini"):
        self.base_url = (base_url or os.getenv("BUILDFORGE_OPENAI_BASE") or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.getenv("BUILDFORGE_OPENAI_KEY") or os.getenv("OPENAI_API_KEY") or ""
        self.model = model
    def is_alive(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            return httpx.get(f"{self.base_url}/models", headers=headers, timeout=5.0).status_code < 500
        except Exception:
            return False
    def chat(self, messages: list, stream: bool = False) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key: headers["Authorization"] = f"Bearer {self.api_key}"
        r = httpx.post(f"{self.base_url}/chat/completions", headers=headers,
                       json={"model": self.model, "messages": messages, "temperature": 0.2}, timeout=600.0)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
