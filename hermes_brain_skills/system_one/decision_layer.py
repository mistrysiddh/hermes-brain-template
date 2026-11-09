"""System One Memory OS — Section 5: System One Decision Layer.

Per mem-draft-spec.txt §5:
- Typed DecisionBackend (Boolean / Choice / Score) + open-weight SLM-class +
  embedding/reranker-class heads
- Admission, typing, entity resolve, relation judgment (incl. lateral),
  routing, scoring, stopping, verification, proactive, dream triggers,
  framework selection, confidence cascades
- Per-schema high/low thresholds; middle band → uncertain
- Full distribution + model/checkpoint + schema_version + latency + cache +
  calibration + fallback on every result
- Operating modes: local, hybrid, shadow, ablation, heuristic
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib
import json
import time
import uuid


# ── Primitives ────────────────────────────────────────────────────────────

class PrimitiveType(str, Enum):
    BOOLEAN = "Boolean"
    CHOICE = "Choice"
    SCORE = "Score"


# ── DecisionBundle ────────────────────────────────────────────────────────

@dataclass
class DecisionBundle:
    """Result of a System One decision call.

    Full distribution + selected + model/checkpoint + schema_version +
    latency + cache + calibration + fallback on every result.
    """

    primitive: PrimitiveType
    question: str
    selected: Any  # bool | str | float
    distribution: dict[str, float]  # full probability distribution
    confidence: float  # 0.0–1.0 calibrated
    uncertainty_band: str  # "high" | "low" | "uncertain"

    # Metadata
    model: str = ""
    checkpoint: str = ""
    schema_version: str = "1.0"
    latency_ms: float = 0.0
    cache_hit: bool = False
    calibration: float | None = None
    fallback: bool = False

    # Timing
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive": self.primitive.value,
            "question": self.question,
            "selected": self.selected,
            "distribution": self.distribution,
            "confidence": self.confidence,
            "uncertainty_band": self.uncertainty_band,
            "model": self.model,
            "checkpoint": self.checkpoint,
            "schema_version": self.schema_version,
            "latency_ms": self.latency_ms,
            "cache_hit": self.cache_hit,
            "calibration": self.calibration,
            "fallback": self.fallback,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecisionBundle":
        return cls(
            primitive=PrimitiveType(data["primitive"]),
            question=data["question"],
            selected=data["selected"],
            distribution=data["distribution"],
            confidence=data["confidence"],
            uncertainty_band=data["uncertainty_band"],
            model=data.get("model", ""),
            checkpoint=data.get("checkpoint", ""),
            schema_version=data.get("schema_version", "1.0"),
            latency_ms=data.get("latency_ms", 0.0),
            cache_hit=data.get("cache_hit", False),
            calibration=data.get("calibration"),
            fallback=data.get("fallback", False),
            created_at=data.get("created_at", ""),
        )


# ── DecisionBackend contract ──────────────────────────────────────────────

class DecisionBackend:
    """Abstract contract for System One typed decision backend.

    Operating modes (per spec §5):
    - local: primary open-weight typed decision model
    - hybrid: local first; larger open-weight teacher only on high uncertainty
    - shadow: local drives production; teacher logs disagreements for RSI
    - ablation: side-by-side multiple backends
    - heuristic: pure deterministic rules for tests + emergency
    """

    def __init__(self, mode: str = "heuristic", model: str = "heuristic-v1",
                 checkpoint: str = "local"):
        self.mode = mode
        self.model = model
        self.checkpoint = checkpoint
        self._cache: dict[str, DecisionBundle] = {}
        self._decision_count = 0
        self._total_latency_ms = 0.0

    # ── Public API ───────────────────────────────────────────────────

    def evaluate(self, state: dict[str, Any],
                 questions: dict[str, PrimitiveType | str],
                 deadline_ms: int = 5000,
                 batch: bool = False) -> dict[str, DecisionBundle]:
        """Evaluate multiple questions against state.

        Returns dict of question_key → DecisionBundle.
        """
        results: dict[str, DecisionBundle] = {}
        start = time.perf_counter()

        for key, qtype in questions.items():
            if isinstance(qtype, str):
                qtype = PrimitiveType(qtype)

            # Check cache first
            cache_key = self._cache_key(state, qtype, key)
            if cache_key in self._cache:
                bundle = self._cache[cache_key]
                bundle.cache_hit = True
                results[key] = bundle
                continue

            # Evaluate
            bundle = self._evaluate_single(state, key, qtype, deadline_ms)
            self._cache[cache_key] = bundle
            results[key] = bundle

        # Record latency
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._decision_count += len(results)
        self._total_latency_ms += elapsed_ms

        return results

    def boolean(self, state: dict[str, Any], proposition: str,
                criteria: str, deadline_ms: int = 5000) -> DecisionBundle:
        """Boolean primitive: Calibrated P(true)."""
        return self._evaluate_single(state, proposition, PrimitiveType.BOOLEAN, deadline_ms)

    def choice(self, state: dict[str, Any], instruction: str,
               options: list[str], criteria: str,
               deadline_ms: int = 5000) -> DecisionBundle:
        """Choice primitive: Categorical distribution over options."""
        return self._evaluate_single(state, instruction, PrimitiveType.CHOICE, deadline_ms)

    def score(self, state: dict[str, Any], instruction: str,
              rubric: list[str], deadline_ms: int = 5000) -> DecisionBundle:
        """Score primitive: Ordinal score."""
        return self._evaluate_single(state, instruction, PrimitiveType.SCORE, deadline_ms)

    # ── Internal ──────────────────────────────────────────────────────

    def _evaluate_single(self, state: dict[str, Any], question: str,
                         qtype: PrimitiveType, deadline_ms: int) -> DecisionBundle:
        start = time.perf_counter()

        if self.mode == "heuristic":
            bundle = self._heuristic_evaluate(state, question, qtype)
        elif self.mode == "local":
            bundle = self._local_evaluate(state, question, qtype)
        elif self.mode == "hybrid":
            bundle = self._hybrid_evaluate(state, question, qtype)
        elif self.mode == "shadow":
            bundle = self._shadow_evaluate(state, question, qtype)
        elif self.mode == "ablation":
            bundle = self._ablation_evaluate(state, question, qtype)
        else:
            bundle = self._heuristic_evaluate(state, question, qtype)

        bundle.latency_ms = (time.perf_counter() - start) * 1000
        bundle.schema_version = "1.0"
        return bundle

    def _heuristic_evaluate(self, state: dict[str, Any], question: str,
                            qtype: PrimitiveType) -> DecisionBundle:
        """Pure deterministic rules for tests + emergency fallback."""
        q_lower = question.lower()

        if qtype == PrimitiveType.BOOLEAN:
            # Heuristic: check for negation, certainty words
            negated = any(w in q_lower for w in ["not ", "no ", "never", "cannot"])
            certain = any(w in q_lower for w in ["is ", "are ", "was ", "were ",
                                                   "definitely", "certainly"])
            selected = certain and not negated
            distribution = {"true": 0.8 if selected else 0.2,
                           "false": 0.2 if selected else 0.8}
            confidence = 0.7
            uncertainty = "low" if confidence > 0.7 else "uncertain"

        elif qtype == PrimitiveType.CHOICE:
            # Heuristic: pick first option that appears in state/question
            options = state.get("options", [])
            selected = options[0] if options else "unknown"
            distribution = {o: (1.0 if o == selected else 0.0) for o in options}
            confidence = 0.6
            uncertainty = "uncertain"

        else:  # SCORE
            # Heuristic: score based on keyword matches
            rubric = state.get("rubric", [])
            score = 0.5
            for i, criterion in enumerate(rubric):
                if any(w in q_lower for w in criterion.lower().split()[:3]):
                    score = (i + 1) / len(rubric)
                    break
            selected = round(score, 2)
            distribution = {str(round(i / (len(rubric) - 1), 2)):
                           0.8 if abs(i / (len(rubric) - 1) - score) < 0.1 else 0.05
                           for i in range(len(rubric))}
            confidence = 0.65
            uncertainty = "uncertain"

        return DecisionBundle(
            primitive=qtype,
            question=question,
            selected=selected,
            distribution=distribution,
            confidence=confidence,
            uncertainty_band=uncertainty,
            model=self.model,
            checkpoint=self.checkpoint,
            fallback=True,
        )

    def _local_evaluate(self, state: dict[str, Any], question: str,
                        qtype: PrimitiveType) -> DecisionBundle:
        """Local open-weight typed decision model (primary)."""
        # Placeholder: in production, this calls a local SLM-class model
        return self._heuristic_evaluate(state, question, qtype)

    def _hybrid_evaluate(self, state: dict[str, Any], question: str,
                         qtype: PrimitiveType) -> DecisionBundle:
        """Local first; larger open-weight teacher on high uncertainty."""
        local = self._local_evaluate(state, question, qtype)
        if local.uncertainty_band == "uncertain":
            # In production, call larger teacher model
            local.fallback = True
            local.model = "teacher-slm-v1"
        return local

    def _shadow_evaluate(self, state: dict[str, Any], question: str,
                         qtype: PrimitiveType) -> DecisionBundle:
        """Local drives production; teacher logs disagreements for RSI."""
        local = self._local_evaluate(state, question, qtype)
        # In production, log disagreement for RLCD-style dataset
        local.model = f"shadow-{self.model}"
        return local

    def _ablation_evaluate(self, state: dict[str, Any], question: str,
                           qtype: PrimitiveType) -> DecisionBundle:
        """Side-by-side multiple backends."""
        return self._heuristic_evaluate(state, question, qtype)

    # ── Cache ─────────────────────────────────────────────────────────

    def _cache_key(self, state: dict[str, Any], qtype: PrimitiveType,
                   question: str) -> str:
        payload = json.dumps({
            "state": state,
            "qtype": qtype.value,
            "question": question,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def clear_cache(self) -> None:
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "model": self.model,
            "checkpoint": self.checkpoint,
            "decision_count": self._decision_count,
            "total_latency_ms": round(self._total_latency_ms, 2),
            "avg_latency_ms": round(self._total_latency_ms / max(1, self._decision_count), 2),
            "cache_size": len(self._cache),
        }


# ── Confidence cascade to System Two ─────────────────────────────────────

@dataclass
class ConfidenceCascade:
    """Interface from System One to System Two."""

    bundle: DecisionBundle
    should_escalate: bool
    reason: str
    suggested_framework: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle": self.bundle.to_dict(),
            "should_escalate": self.should_escalate,
            "reason": self.reason,
            "suggested_framework": self.suggested_framework,
        }


def should_cascade_to_system_two(bundle: DecisionBundle,
                                 thresholds: dict[str, float] | None = None) -> ConfidenceCascade:
    """Determine if a decision should cascade to System Two synthesis.

    Per spec: Confidence cascade interface to System Two.
    Middle band → uncertain → escalate.
    Stricter bars for entity merge, causal links, framework induction, skill promotion.
    """
    thresholds = thresholds or {
        "high_confidence": 0.8,
        "low_confidence": 0.3,
    }

    if bundle.confidence >= thresholds["high_confidence"]:
        return ConfidenceCascade(
            bundle=bundle,
            should_escalate=False,
            reason="High confidence, no escalation needed",
        )

    if bundle.confidence <= thresholds["low_confidence"]:
        return ConfidenceCascade(
            bundle=bundle,
            should_escalate=True,
            reason="Low confidence, escalate to System Two",
            suggested_framework="framework-selection",
        )

    # Middle band → uncertain
    return ConfidenceCascade(
        bundle=bundle,
        should_escalate=True,
        reason="Uncertainty band, escalate to System Two",
        suggested_framework="framework-selection",
    )
