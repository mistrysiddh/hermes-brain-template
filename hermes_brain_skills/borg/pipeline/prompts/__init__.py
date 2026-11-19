"""Borg pipeline sub-prompts — extracted template files for modularity.

Each sub-prompt is a separate template that agents load at runtime,
allowing independent editing and versioning of the prompting logic.
"""

__version__ = "1.0.0"

__all__ = [
    "load_prompt",
    "S1_UNPACK_PROMPT",
    "S1_CHECKSUM_PROMPT",
    "S1_CLASSIFY_PROMPT",
]

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


# ── S1 Ingestor sub-prompts ──────────────────────────────────────────────

S1_UNPACK_PROMPT = load_prompt("s1_unpack_prompt")
S1_CHECKSUM_PROMPT = load_prompt("s1_checksum_prompt")
S1_CLASSIFY_PROMPT = load_prompt("s1_classify_prompt")
