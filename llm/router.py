from __future__ import annotations
import os
from core.types import LlmBackend
from llm.ollama import OllamaClient
from llm.openai_compat import OpenAICompatClient
from llm.gguf_local import GgufLocalClient

def make_llm(backend, model=None, **kwargs):
    b = backend.value if isinstance(backend, LlmBackend) else str(backend or "none").lower()
    model = model or os.getenv("BUILDFORGE_MODEL") or "qwen2.5:7b"
    if b in ("none", "", "off"): return None
    if b == "ollama":
        return OllamaClient(base_url=kwargs.get("base_url") or os.getenv("BUILDFORGE_OLLAMA_URL") or "http://127.0.0.1:11434", model=model)
    if b in ("openai", "cloud", "lmstudio"):
        return OpenAICompatClient(base_url=kwargs.get("base_url"), api_key=kwargs.get("api_key"), model=model)
    if b == "gguf":
        return GgufLocalClient(model_path=kwargs.get("model_path"))
    raise ValueError(f"unknown llm backend: {b}")
