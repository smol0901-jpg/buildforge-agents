from __future__ import annotations
"""
Host profile defaults for the owner's Windows machine (from DevTools_Report + user notes).

Detected / declared:
  - Windows + Windows SDK 10.1.26100.7705
  - Node.js 22.20.0 · npm 11.16.0
  - Python 3.11.9
  - Git 2.53
  - Ollama at %LOCALAPPDATA%\\Programs\\Ollama
  - Models: hf.co/prism-ml/Bonsai-8B-gguf:Q1_0 (primary), Bonsai-1.7B-gguf:Q1_0 (light)
  - LAN RTT ~147ms (local Ollama — fine for neural mode)
  - Anti-freeze caps: CPU 97% · RAM 96%
"""
from __future__ import annotations

import os
from pathlib import Path

# Primary local model (user pulled successfully)
DEFAULT_OLLAMA_MODEL = os.getenv(
    "BUILDFORGE_MODEL",
    "hf.co/prism-ml/Bonsai-8B-gguf:Q1_0",
)
LIGHT_OLLAMA_MODEL = os.getenv(
    "BUILDFORGE_MODEL_LIGHT",
    "hf.co/prism-ml/Bonsai-1.7B-gguf:Q1_0",
)
DEFAULT_LLM = os.getenv("BUILDFORGE_LLM", "ollama")
DEFAULT_MODE = os.getenv("BUILDFORGE_MODE", "neural")  # owner has Ollama
DEFAULT_OLLAMA_URL = os.getenv("BUILDFORGE_OLLAMA_URL", "http://127.0.0.1:11434")
MAX_FIX_RETRIES = int(os.getenv("BUILDFORGE_MAX_FIX_RETRIES", "2"))

# Anti-freeze (user request)
CPU_CRITICAL = float(os.getenv("BUILDFORGE_CPU_CRITICAL", "97"))
RAM_CRITICAL = float(os.getenv("BUILDFORGE_RAM_CRITICAL", "96"))
CPU_RECOVER = float(os.getenv("BUILDFORGE_CPU_RECOVER", "90"))
RAM_RECOVER = float(os.getenv("BUILDFORGE_RAM_RECOVER", "90"))

PHONE_PORT = int(os.getenv("BUILDFORGE_PHONE_PORT", "8787"))


def ollama_install_dir() -> Path | None:
    local = os.environ.get("LOCALAPPDATA") or ""
    p = Path(local) / "Programs" / "Ollama"
    return p if p.exists() else None


def apply_env_defaults() -> dict:
    """Set process env defaults if user didn't override. Safe to call at startup."""
    defaults = {
        "BUILDFORGE_LLM": DEFAULT_LLM,
        "BUILDFORGE_MODEL": DEFAULT_OLLAMA_MODEL,
        "BUILDFORGE_MODEL_LIGHT": LIGHT_OLLAMA_MODEL,
        "BUILDFORGE_MODE": DEFAULT_MODE,
        "BUILDFORGE_OLLAMA_URL": DEFAULT_OLLAMA_URL,
        "BUILDFORGE_MAX_FIX_RETRIES": str(MAX_FIX_RETRIES),
        "BUILDFORGE_CPU_CRITICAL": str(CPU_CRITICAL),
        "BUILDFORGE_RAM_CRITICAL": str(RAM_CRITICAL),
        "BUILDFORGE_CPU_RECOVER": str(CPU_RECOVER),
        "BUILDFORGE_RAM_RECOVER": str(RAM_RECOVER),
        "BUILDFORGE_GUARD_ENABLED": os.getenv("BUILDFORGE_GUARD_ENABLED", "1"),
        "BUILDFORGE_PHONE_PORT": str(PHONE_PORT),
    }
    applied = {}
    for k, v in defaults.items():
        if k not in os.environ or os.environ.get(k, "") == "":
            os.environ[k] = v
            applied[k] = v
    return applied


def profile_summary() -> dict:
    return {
        "llm": os.getenv("BUILDFORGE_LLM", DEFAULT_LLM),
        "model": os.getenv("BUILDFORGE_MODEL", DEFAULT_OLLAMA_MODEL),
        "model_light": os.getenv("BUILDFORGE_MODEL_LIGHT", LIGHT_OLLAMA_MODEL),
        "mode": os.getenv("BUILDFORGE_MODE", DEFAULT_MODE),
        "ollama_url": os.getenv("BUILDFORGE_OLLAMA_URL", DEFAULT_OLLAMA_URL),
        "ollama_dir": str(ollama_install_dir() or ""),
        "max_fix_retries": int(os.getenv("BUILDFORGE_MAX_FIX_RETRIES", str(MAX_FIX_RETRIES))),
        "cpu_critical": float(os.getenv("BUILDFORGE_CPU_CRITICAL", str(CPU_CRITICAL))),
        "ram_critical": float(os.getenv("BUILDFORGE_RAM_CRITICAL", str(RAM_CRITICAL))),
        "node": "22.x (from DevTools report)",
        "python": "3.11.9 (from DevTools report)",
        "windows_sdk": "10.1.26100.7705",
    }
