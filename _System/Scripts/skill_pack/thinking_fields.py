"""Hermes Brain — Skill Pack Thinking Fields.

Captures free-text reasoning from the learner alongside answers,
supporting:

- Free-text reasoning — learners explain reasoning in their own words.
- Confidence tracking — learner states confidence alongside answers.
- Multi-entry probe — from simple questions through complex reasoning.
- Understanding boundary detection — maps where knowledge ends.

Thinking fields are stored as JSONL records under
<vault>/_System/SkillPacks/thinking_fields/.

Multi-harness compliant: stdlib-only, --dry-run default, --apply.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any

VAULT = None

TF_DIR = "_System/SkillPacks/thinking_fields"
RECORDS_FILE = "thinking_fields.jsonl"


def init_paths(vault_path):
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


def _tf_dir(vault):
    return os.path.join(vault, TF_DIR)


def _ensure_dir(vault):
    d = _tf_dir(vault)
    os.makedirs(d, exist_ok=True)
    return d


def _read_jsonl(path):
    records = []
    if not os.path.exists(path):
        return records
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def capture_thinking_field(
    question_id: str,
    answer: str,
    reasoning: str,
    confidence: float | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Capture a learner's thinking field (free-text reasoning).

    Args:
        question_id: ID of the question being answered.
        answer: The learner's answer.
        reasoning: Free-text reasoning explaining the answer.
        confidence: Optional confidence score (0.0–1.0).
        dry_run: If True, the record is returned but not written.

    Returns the created thinking field record.

    """
    record = {
        "id": str(uuid.uuid4()),
        "type": "thinking_field",
        "question_id": question_id,
        "answer": answer,
        "reasoning": reasoning,
        "confidence": confidence,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    if dry_run:
        return record

    _ensure_dir(VAULT)
    path = os.path.join(_tf_dir(VAULT), RECORDS_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def list_thinking_fields(vault, limit: int = 50) -> list[dict[str, Any]]:
    """List all thinking field records."""
    path = os.path.join(_tf_dir(vault), RECORDS_FILE)
    records = _read_jsonl(path)
    return records[-limit:] if limit else records


def detect_understanding_boundary(
    thinking_fields: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect where the learner's understanding ends.

    Analyzes thinking fields for low confidence, short reasoning,
    or missing reasoning connectives to identify understanding gaps.

    Returns:
        {
            "boundary_indicators": list[str],
            "low_confidence_questions": list[str],
            "weak_reasoning_questions": list[str],
            "summary": str,
        }

    """
    low_confidence: list[str] = []
    weak_reasoning: list[str] = []
    indicators: list[str] = []

    for tf in thinking_fields:
        qid = tf.get("question_id", "unknown")
        conf = tf.get("confidence")
        reasoning = tf.get("reasoning", "")

        if conf is not None and conf < 0.5:
            low_confidence.append(qid)
            indicators.append(f"Low confidence ({conf}) on {qid}")

        if len(reasoning.strip()) < 20:
            weak_reasoning.append(qid)
            indicators.append(f"Short reasoning on {qid}")

        if not any(
            c in reasoning.lower()
            for c in ["because", "since", "therefore", "however"]
        ):
            weak_reasoning.append(qid)
            indicators.append(f"No reasoning connective on {qid}")

    summary = (
        f"Analyzed {len(thinking_fields)} thinking fields. "
        f"{len(low_confidence)} low-confidence, "
        f"{len(weak_reasoning)} weak-reasoning entries."
    )

    return {
        "boundary_indicators": indicators,
        "low_confidence_questions": low_confidence,
        "weak_reasoning_questions": weak_reasoning,
        "summary": summary,
    }
