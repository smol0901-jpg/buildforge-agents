"""NEURAL_ARCHITECT_PREMIUM++ kernel for BuildForge."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def load_text(name: str) -> str:
    p = ROOT / name
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def system_prompt(extra: str = "") -> str:
    parts = [
        load_text("BUILDFORGE_PERSONA.md"),
        "\n---\n# ACTIVATION\n" + load_text("00_ACTIVATION.md"),
        "\n---\n# IDENTITY\n" + load_text("01_IDENTITY.md")[:3000],
        "\n---\n# DECOMPOSITION\n" + load_text("03_DECOMPOSITION_PROTOCOL.md")[:2500],
        "\n---\n# TRUTH CHAIN\n" + load_text("04_TRUTH_VERIFICATION_CHAIN.md")[:2500],
        "\n---\n# VECTOR CORRECTION\n" + load_text("05_VECTOR_CORRECTION.md")[:1500],
    ]
    v8 = load_text("v8.txt")
    if v8: parts.append("\n---\n# NAP++ v8 (excerpt)\n" + v8[:8000])
    if extra: parts.append("\n---\n# TASK\n" + extra)
    return "\n".join(parts)

KERNEL_NAME = "NEURAL_ARCHITECT_PREMIUM++ BuildForge"
KERNEL_VERSION = "8.4.00-buildforge"
AUTHOR = "Смолянинов Александр Вячеславович / ASV_PROD"
CONTACTS = {"telegram": "@ASV_prod", "vk": "https://vk.com/smolyaninovchef"}
