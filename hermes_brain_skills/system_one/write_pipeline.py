"""System One Memory OS — Section 6: Write Pipeline.

Per mem-draft-spec.txt §6:
1. Capture uniform envelope (source_type, URI, external_id, content, observed_at, metadata, ACL, scope)
2. Content hash; exact duplicates reference existing artifact
3. Source-aware segmentation (text/conversation/code/vault)
4. Preserve-first admission (controls hot/cold/salience/review/proactive/framework-eligibility)
5. Cheap deterministic gates first (secrets, near-duplicates, injection patterns, pure status noise)
6. Overlapping multi-label typing (Sys1 independent probs + secondary tags incl. framework/skill)
7. Entity extraction: deterministic first (metadata, IDs, symbols, URLs, paths, known aliases); generative fallback only for hard NL
8. Conservative entity resolution: exact alias / normalized / shared IDs / lexical / vector / shared context; Sys1 same/possibly/different; auto-merge only at extremely high calibrated threshold; else Inbox
9. Bounded relation candidate generation: vector neighbors + keyword + shared entities + nearby times + same source/session/project + code refs + analogical seeds; tight caps; RRF fusion
10. Relation view materialization (deterministic + model-judged)
11. Evolution detection: non-destructive version_relation emission
12. Index maintenance: dual FTS, vectors, adjacency, entity aliases, temporal indexes, active/current facts, procedural/skill indexes, access weights, framework indexes
13. Vault-mode extras: human-reviewed proposals land in Inbox; source content-hash verified before any model call; no silent write-back
14. Continuous file watcher + hash-based deduplication
15. Cross-device: human-readable projection sync or lightweight shared-context loop
16. Write policies shadow-logged and evolvable
17. Optional mental-model or skill attachment / induction trigger at write time
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib
import json
import os
import re
import time

from hermes_brain_skills.system_one.models import (
    Record, RecordKind, create_record, record_to_json, record_from_json,
)
from hermes_brain_skills.system_one.storage import CanonicalStore


# ── Envelope ──────────────────────────────────────────────────────────────

@dataclass
class Envelope:
    """Uniform capture envelope emitted by watchers/connectors/CLI/adapters."""
    source_type: str
    uri: str
    external_id: str | None
    content: str
    observed_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    acl: str | None = None
    scope: str | None = None
    connector: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "uri": self.uri,
            "external_id": self.external_id,
            "content": self.content,
            "observed_at": self.observed_at,
            "metadata": self.metadata,
            "acl": self.acl,
            "scope": self.scope,
            "connector": self.connector,
        }


# ── Deterministic gates ──────────────────────────────────────────────────

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9+/=]{20,}"),
    re.compile(r"(?i)(ssh-rsa|ssh-ed25519)\s+[A-Za-z0-9+/=]+"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?\S{8,}"),
]

INJECTION_PATTERNS = [
    re.compile(r"(?i)(ignore\s+previous|disregard\s+all|system\s*:\s*|assistant\s*:\s*|<system>|</system>)"),
    re.compile(r"(?i)(jailbreak|prompt\s+injection|override\s+safety)"),
]


def cheap_deterministic_gates(envelope: Envelope) -> dict[str, Any]:
    """Step 5: Cheap deterministic gates before any model call."""
    result: dict[str, Any] = {
        "admit": True,
        "secrets_found": [],
        "injection_found": [],
        "near_duplicate": False,
        "pure_status_noise": False,
        "reasons": [],
    }

    content = envelope.content

    # Secrets scan
    for pat in SECRET_PATTERNS:
        if pat.search(content):
            result["secrets_found"].append(pat.pattern[:40])
            result["admit"] = False
            result["reasons"].append("secret_detected")

    # Injection scan
    for pat in INJECTION_PATTERNS:
        if pat.search(content):
            result["injection_found"].append(pat.pattern[:40])
            result["admit"] = False
            result["reasons"].append("injection_pattern_detected")

    # Pure status noise (very short, no meaningful content)
    if len(content.strip()) < 3:
        result["pure_status_noise"] = True
        result["reasons"].append("pure_status_noise")
        # Not auto-reject, just flagged

    return result


def content_hash(content: str) -> str:
    """SHA-256 content hash for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ── Source-aware segmentation ─────────────────────────────────────────────

class SegmentType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    SENTENCE = "sentence"
    TURN = "turn"
    CLAUSE = "clause"
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    TYPE = "type"
    MACRO = "macro"
    MODULE = "module"
    CALL = "call"
    IMPORT = "import"
    BUILD = "build"


def segment_text(content: str, source_type: str) -> list[dict[str, Any]]:
    """Step 3: Source-aware segmentation."""
    segments: list[dict[str, Any]] = []

    if source_type in ("text", "note", "markdown", "vault"):
        # Heading-aware + frontmatter for vaults
        lines = content.split("\n")
        current_segment: list[str] = []
        current_type = SegmentType.PARAGRAPH

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                if current_segment:
                    segments.append({
                        "type": current_type,
                        "content": "\n".join(current_segment),
                    })
                    current_segment = []
                current_type = SegmentType.HEADING
                current_segment.append(line)
            elif stripped.startswith(("- ", "* ", "+ ")):
                if current_segment and current_type != SegmentType.LIST:
                    segments.append({
                        "type": current_type,
                        "content": "\n".join(current_segment),
                    })
                    current_segment = []
                current_type = SegmentType.LIST
                current_segment.append(line)
            elif stripped == "":
                if current_segment:
                    segments.append({
                        "type": current_type,
                        "content": "\n".join(current_segment),
                    })
                    current_segment = []
                    current_type = SegmentType.PARAGRAPH
            else:
                current_segment.append(line)

        if current_segment:
            segments.append({
                "type": current_type,
                "content": "\n".join(current_segment),
            })

    elif source_type == "conversation":
        # Preserve turns ± atomic clauses
        # Simple turn split on common patterns
        turns = re.split(r"(?i)(?:user|assistant|system):\s*", content)
        for turn in turns:
            turn = turn.strip()
            if not turn:
                continue
            # Split into atomic clauses
            clauses = re.split(r"(?<=[.!?])\s+", turn)
            for clause in clauses:
                clause = clause.strip()
                if clause:
                    segments.append({"type": SegmentType.CLAUSE, "content": clause})

    elif source_type == "code":
        # AST extraction stub: functions/methods/classes/types/macros/modules/calls/imports/build constructs
        # Whole-file fallback
        segments.append({"type": SegmentType.MODULE, "content": content})

    else:
        # Sys1 boundary only if structure insufficient
        segments.append({"type": SegmentType.SENTENCE, "content": content})

    return segments


# ── Preserve-first admission ──────────────────────────────────────────────

@dataclass
class AdmissionDecision:
    """Step 4: Preserve-first admission controls."""
    admit: bool = True
    hot: bool = False
    cold: bool = False
    salience: float = 0.5
    review: bool = False
    proactive: bool = False
    framework_eligible: bool = False
    inbox: bool = False
    reasons: list[str] = field(default_factory=list)


def admission_control(
    envelope: Envelope,
    gate_result: dict[str, Any],
    segments: list[dict[str, Any]],
) -> AdmissionDecision:
    """Step 4: Preserve-first admission. Never irreversibly discard."""
    decision = AdmissionDecision()

    if not gate_result["admit"]:
        decision.admit = False
        decision.inbox = True
        decision.reasons.extend(gate_result["reasons"])
        return decision

    # Default: admit, mark for review
    decision.review = True

    # Salience based on content length and source type
    content_len = len(envelope.content)
    if content_len > 1000:
        decision.salience = 0.8
        decision.hot = True
    elif content_len > 200:
        decision.salience = 0.5
    else:
        decision.salience = 0.2
        decision.cold = True

    # Framework eligibility based on source type
    if envelope.source_type in ("code", "vault", "note"):
        decision.framework_eligible = True

    # Proactive for high-salience
    if decision.salience > 0.7:
        decision.proactive = True

    return decision


# ── Multi-label typing ────────────────────────────────────────────────────

MEMORY_TYPE_LABELS = [
    "episodic", "semantic", "procedural", "preference",
    "decision", "commitment", "open-loop", "gotcha",
    "convention", "task", "contact", "reference",
    "framework", "skill",
]


def multi_label_typing(
    envelope: Envelope,
    segments: list[dict[str, Any]],
    decision_backend: Any | None = None,
) -> dict[str, Any]:
    """Step 6: Overlapping multi-label typing.

    Sys1 independent probs + secondary tags including framework/skill.
    """
    labels: dict[str, float] = {}
    content_lower = envelope.content.lower()

    # Deterministic keyword-based typing
    keyword_map = {
        "decision": ["decide", "decision", "choose", "select", "option"],
        "commitment": ["commit", "promise", "will do", "agreed"],
        "task": ["todo", "task", "action item", "next step", "action"],
        "gotcha": ["gotcha", "trap", "pitfall", "warning", "careful"],
        "convention": ["convention", "standard", "guideline", "rule"],
        "framework": ["framework", "model", "approach", "methodology"],
        "skill": ["skill", "ability", "capability", "expertise"],
        "reference": ["ref", "reference", "source", "link", "url"],
        "contact": ["contact", "person", "people", "team", "colleague"],
        "procedural": ["procedure", "process", "workflow", "step-by-step"],
        "preference": ["prefer", "like", "dislike", "favorite"],
        "semantic": ["concept", "idea", "meaning", "definition"],
        "episodic": ["happened", "occurred", "event", "session", "meeting"],
        "open-loop": ["open", "pending", "unresolved", "todo"],
    }

    for label, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            labels[label] = min(score / len(keywords), 1.0)

    # Sys1 independent probs (if decision backend available)
    if decision_backend is not None:
        try:
            bundles = decision_backend.evaluate(
                {"content": envelope.content},
                {label: "Choice" for label in MEMORY_TYPE_LABELS},
                deadline_ms=2000,
            )
            for label, bundle in bundles.items():
                if bundle.selected:
                    labels[label] = bundle.confidence
        except Exception:
            pass  # Fall back to deterministic only

    return {
        "labels": labels,
        "primary": max(labels, key=labels.get) if labels else "semantic",
        "secondary": sorted(labels, key=labels.get, reverse=True)[:5],
    }


# ── Entity extraction ─────────────────────────────────────────────────────

def deterministic_entity_extraction(content: str) -> list[dict[str, Any]]:
    """Step 7: Deterministic entity extraction first."""
    entities: list[dict[str, Any]] = []

    # URLs
    for m in re.finditer(r"https?://[^\s<>\"]+", content):
        entities.append({
            "type": "URL",
            "value": m.group(0),
            "offset": m.start(),
            "confidence": 1.0,
            "method": "deterministic",
        })

    # File paths
    for m in re.finditer(r"(?:/[\w/.-]+|[\w]+\.[\w]+)", content):
        val = m.group(0)
        if "." in val and len(val) > 3:
            entities.append({
                "type": "PATH",
                "value": val,
                "offset": m.start(),
                "confidence": 0.8,
                "method": "deterministic",
            })

    # Email addresses
    for m in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", content):
        entities.append({
            "type": "EMAIL",
            "value": m.group(0),
            "offset": m.start(),
            "confidence": 1.0,
            "method": "deterministic",
        })

    # Code symbols (backtick-quoted)
    for m in re.finditer(r"`([^`]+)`", content):
        entities.append({
            "type": "SYMBOL",
            "value": m.group(1),
            "offset": m.start(),
            "confidence": 0.7,
            "method": "deterministic",
        })

    return entities


# ── Write pipeline result ─────────────────────────────────────────────────

@dataclass
class WriteResult:
    """Result of the full write pipeline."""
    envelope: Envelope
    segments: list[dict[str, Any]]
    gate_result: dict[str, Any]
    admission: AdmissionDecision
    typing: dict[str, Any]
    entities: list[dict[str, Any]]
    artifact_id: str | None = None
    observation_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    version_relation_ids: list[str] = field(default_factory=list)
    inbox_item: bool = False
    warnings: list[str] = field(default_factory=list)


class WritePipeline:
    """Full write pipeline (Section 6)."""

    def __init__(self, store: Any | None = None, decision_backend: Any | None = None):
        self.store = store
        self.decision_backend = decision_backend
        self._artifact_cache: dict[str, str] = {}  # content_hash -> artifact_id

    def process(self, envelope: Envelope) -> WriteResult:
        """Run the full write pipeline (Steps 1-17)."""
        result = WriteResult(
            envelope=envelope,
            segments=[],
            gate_result={},
            admission=AdmissionDecision(),
            typing={},
            entities=[],
        )

        # Step 1: Capture uniform envelope (already done via Envelope)
        # Step 2: Content hash; exact duplicates reference existing artifact
        chash = content_hash(envelope.content)
        if chash in self._artifact_cache:
            result.artifact_id = self._artifact_cache[chash]
            result.warnings.append("exact_duplicate_referenced")
            result.admission = AdmissionDecision(admit=False, inbox=True)
            return result

        # Step 3: Source-aware segmentation
        result.segments = segment_text(envelope.content, envelope.source_type)

        # Step 5: Cheap deterministic gates first
        result.gate_result = cheap_deterministic_gates(envelope)

        # Step 4: Preserve-first admission
        result.admission = admission_control(envelope, result.gate_result, result.segments)

        # Step 6: Overlapping multi-label typing
        result.typing = multi_label_typing(envelope, result.segments, self.decision_backend)

        # Step 7: Entity extraction (deterministic first)
        result.entities = deterministic_entity_extraction(envelope.content)

        # Step 8: Conservative entity resolution (stub - would use Sys1)
        # Step 9-11: Relation generation, materialization, evolution detection (stub)
        # Step 12: Index maintenance (handled by store)
        # Step 13: Vault-mode extras
        if envelope.scope == "vault" and result.admission.review:
            result.inbox_item = True
            result.warnings.append("vault_mode_human_review_required")

        # Step 14: Continuous file watcher (external)
        # Step 15: Cross-device sync (external)
        # Step 16: Write policies shadow-logged (external)
        # Step 17: Mental-model/skill induction trigger (external)

        # Write to store if available
        if self.store and result.admission.admit and not result.inbox_item:
            try:
                artifact = create_record(
                    RecordKind.ARTIFACT,
                    content={"content": envelope.content, "mime_type": "text/plain"},
                    provenance={"source_uri": envelope.uri, "captured_at": envelope.observed_at},
                )
                self.store.write_record(artifact)
                result.artifact_id = artifact.record_id
                self._artifact_cache[chash] = artifact.record_id

                # Create observations for segments
                for seg in result.segments:
                    obs = create_record(
                        RecordKind.OBSERVATION,
                        content={"text": seg["content"], "artifact_id": artifact.record_id, "source_span": seg["type"]},
                    )
                    self.store.write_record(obs)
                    result.observation_ids.append(obs.record_id)
            except Exception as e:
                result.warnings.append(f"store_write_failed: {e}")

        return result


# ── Convenience function ─────────────────────────────────────────────────

def process_envelope(
    envelope: Envelope,
    store: Any | None = None,
    decision_backend: Any | None = None,
) -> WriteResult:
    """Convenience function to process a single envelope through the write pipeline."""
    pipeline = WritePipeline(store=store, decision_backend=decision_backend)
    return pipeline.process(envelope)
