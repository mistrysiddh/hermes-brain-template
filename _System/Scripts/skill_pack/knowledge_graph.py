"""Hermes Brain — Skill Pack Knowledge Graph.

Persistent knowledge graph of propositions and reasoning chains,
inspired by LearnHarness's knowledge graph design:

- Propositions: individual claims accumulated over sessions.
- Reasoning chains: premises that lead to claims.
- Cross-session persistence: future sessions read the graph instead
  of starting from scratch.
- Ideas-not-ratings: stores ideas and connections, not ability
  ratings or levels.
- Source session links: graph links back to source teaching sessions.
- Practice material source: practice sessions draw from the graph.

Storage: plain JSONL files under <vault>/_System/SkillPacks/knowledge_graph/
(one JSONL file per proposition/chain type). stdlib-only.

Multi-harness compliant: --vault via init_paths(), --dry-run default,
--apply for human approval.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any

# Deferred vault path — resolved at runtime
VAULT = None

KG_DIR = "_System/SkillPacks/knowledge_graph"
PROPOSITIONS_FILE = "propositions.jsonl"
CHAINS_FILE = "reasoning_chains.jsonl"
SESSIONS_FILE = "source_sessions.jsonl"


def init_paths(vault_path):
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


def _kg_dir(vault):
    return os.path.join(vault, KG_DIR)


def _ensure_dir(vault):
    d = _kg_dir(vault)
    os.makedirs(d, exist_ok=True)
    return d


def _read_jsonl(path):
    """Read all records from a JSONL file."""
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


def _append_jsonl(path, record):
    """Append a single record to a JSONL file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def add_proposition(
    content: str,
    session_id: str | None = None,
    confidence: float | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Add a proposition (individual claim) to the knowledge graph.

    Returns the created proposition record.

    Args:
        content: The claim text.
        session_id: Optional source session link.
        confidence: Optional confidence score (0.0–1.0).
        dry_run: If True, the record is returned but not written.

    """
    record = {
        "id": str(uuid.uuid4()),
        "type": "proposition",
        "content": content,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "confidence": confidence,
    }

    if dry_run:
        return record

    _ensure_dir(VAULT)
    _append_jsonl(os.path.join(_kg_dir(VAULT), PROPOSITIONS_FILE), record)
    return record


def list_propositions(vault, limit: int = 50) -> list[dict[str, Any]]:
    """List all propositions from the knowledge graph."""
    path = os.path.join(_kg_dir(vault), PROPOSITIONS_FILE)
    records = _read_jsonl(path)
    return records[-limit:] if limit else records


def add_reasoning_chain(
    premises: list[str],
    conclusion: str,
    session_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Add a reasoning chain (premises → conclusion) to the graph.

    Returns the created chain record.

    Args:
        premises: List of premise strings.
        conclusion: The derived conclusion string.
        session_id: Optional source session link.
        dry_run: If True, the record is returned but not written.

    """
    record = {
        "id": str(uuid.uuid4()),
        "type": "reasoning_chain",
        "premises": premises,
        "conclusion": conclusion,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
    }

    if dry_run:
        return record

    _ensure_dir(VAULT)
    _append_jsonl(os.path.join(_kg_dir(VAULT), CHAINS_FILE), record)
    return record


def list_reasoning_chains(vault, limit: int = 50) -> list[dict[str, Any]]:
    """List all reasoning chains from the knowledge graph."""
    path = os.path.join(_kg_dir(vault), CHAINS_FILE)
    records = _read_jsonl(path)
    return records[-limit:] if limit else records


def link_session(vault, session_id: str, session_meta: dict | None = None):
    """Record a source session link in the graph."""
    record = {
        "id": session_id,
        "type": "source_session",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "meta": session_meta or {},
    }
    _ensure_dir(vault)
    _append_jsonl(
        os.path.join(_kg_dir(vault), SESSIONS_FILE), record
    )
    return record
