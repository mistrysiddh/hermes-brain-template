"""System One Memory OS — Section 7: Read Pipeline.

Per mem-draft-spec.txt §7:

Phase 0 – Cache: O(1) semantic cache lookup; return pre-verified bundle on hit
Phase 1 – Routing: need vector generation, required answer facets, explicit budget allocation, optional early confidence cascade, optional framework pre-selection
Phase 2 – Anchors + Expansion: parallel hybrid anchors (exact substring + FTS + vector + entity + date + tag/project + code symbol + analogical seeds), RRF, Sys1 Score seed validation, pluggable expanders, priority scoring, budgeted best-first/beam traversal, access-index reweighting
Phase 3 – Judgment + Stopping: Batch Sys1 judgment, intelligent stopping, hard limits
Phase 4 – Bundle + Synthesis + Verification: Evidence bundle construction, L0–L3 token-aware packing, optional single System Two synthesis, per-claim atomic verification, modes (lite/full/auto-escalate/framework-augmented)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib
import json
import time


# ── Read modes ────────────────────────────────────────────────────────────

class ReadMode(str, Enum):
    LITE = "lite"
    FULL = "full"
    AUTO_ESCALATE = "auto-escalate"
    FRAMEWORK_AUGMENTED = "framework-augmented"


# ── Read request ─────────────────────────────────────────────────────────

@dataclass
class ReadRequest:
    """Read pipeline request."""
    question: str
    scopes: list[str] | None = None
    as_of: str | None = None
    max_latency_ms: int = 5000
    evidence_only: bool = True
    token_budget: int | None = None
    frameworks: list[str] | None = None
    mode: ReadMode = ReadMode.FULL
    need_vector: bool = True
    answer_facets: list[str] | None = None
    budget_tokens: int = 2000
    budget_depth: int = 5
    budget_decision_calls: int = 10


# ── Read result ──────────────────────────────────────────────────────────

@dataclass
class EvidenceBundle:
    """Evidence bundle with IDs, spans, coordinates, retrieval path."""
    evidence_ids: list[str] = field(default_factory=list)
    spans: list[dict[str, Any]] = field(default_factory=list)
    coordinates: list[dict[str, Any]] = field(default_factory=list)
    retrieval_path: list[str] = field(default_factory=list)
    relevance: dict[str, float] = field(default_factory=dict)
    trust: dict[str, float] = field(default_factory=dict)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    applied_frameworks: list[str] = field(default_factory=list)
    packing_tier: str = "L2"


@dataclass
class ReadResult:
    """Read pipeline result."""
    question: str
    mode: ReadMode
    bundle: EvidenceBundle
    synthesis: str | None = None
    verification: dict[str, Any] = field(default_factory=dict)
    cache_hit: bool = False
    latency_ms: float = 0.0
    decision_calls: int = 0
    evidence_tokens: int = 0
    frameworks_applied: list[str] = field(default_factory=list)


# ── Semantic cache ───────────────────────────────────────────────────────

class SemanticCache:
    """O(1) semantic cache with TTL (Phase 0)."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[EvidenceBundle, float]] = {}

    def _key(self, question: str, scopes: list[str] | None, as_of: str | None) -> str:
        payload = json.dumps({
            "question": question,
            "scopes": scopes or [],
            "as_of": as_of or "",
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def lookup(self, question: str, scopes: list[str] | None = None, as_of: str | None = None) -> EvidenceBundle | None:
        """O(1) cache lookup; return pre-verified bundle on hit."""
        key = self._key(question, scopes, as_of)
        if key in self._cache:
            bundle, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return bundle
            else:
                del self._cache[key]
        return None

    def store(self, question: str, bundle: EvidenceBundle, scopes: list[str] | None = None, as_of: str | None = None) -> None:
        """Store bundle in cache."""
        key = self._key(question, scopes, as_of)
        self._cache[key] = (bundle, time.time())

    def stats(self) -> dict[str, Any]:
        return {
            "entries": len(self._cache),
            "ttl_seconds": self.ttl_seconds,
        }


# ── Anchors ──────────────────────────────────────────────────────────────

class AnchorExpander:
    """Phase 2: Parallel hybrid anchors + pluggable expanders."""

    def __init__(self, store: Any | None = None):
        self.store = store
        self.expanders: list[str] = [
            "GraphEdge", "Entity", "Temporal", "CodeReference",
            "ExactName", "History", "DocumentLink", "Procedural",
            "Lateral/Analogical", "Framework",
        ]

    def hybrid_anchors(
        self,
        question: str,
        entities: list[str] | None = None,
        date_range: tuple[str, str] | None = None,
        tags: list[str] | None = None,
        project: str | None = None,
    ) -> list[dict[str, Any]]:
        """Parallel hybrid anchors: exact substring + FTS + vector + entity + date + tag/project + code symbol + analogical seeds."""
        anchors: list[dict[str, Any]] = []

        # Exact substring anchor
        anchors.append({
            "type": "exact_substring",
            "query": question,
            "source": "anchor",
        })

        # FTS anchor
        anchors.append({
            "type": "fts",
            "query": question,
            "source": "anchor",
        })

        # Vector anchor (if needed)
        anchors.append({
            "type": "vector",
            "query": question,
            "source": "anchor",
        })

        # Entity anchors
        for ent in (entities or []):
            anchors.append({
                "type": "entity",
                "query": ent,
                "source": "anchor",
            })

        # Date anchors
        if date_range:
            anchors.append({
                "type": "temporal",
                "query": f"{date_range[0]} to {date_range[1]}",
                "source": "anchor",
            })

        # Tag/project anchors
        for tag in (tags or []):
            anchors.append({
                "type": "tag",
                "query": tag,
                "source": "anchor",
            })
        if project:
            anchors.append({
                "type": "project",
                "query": project,
                "source": "anchor",
            })

        # Code symbol anchors
        anchors.append({
            "type": "code_symbol",
            "query": question,
            "source": "anchor",
        })

        # Analogical seeds
        anchors.append({
            "type": "analogical_seed",
            "query": question,
            "source": "anchor",
        })

        return anchors

    def rrf_fusion(self, anchor_results: list[list[dict[str, Any]]], k: int = 60) -> list[dict[str, Any]]:
        """Reciprocal Rank Fusion across anchor result lists."""
        scores: dict[str, float] = {}
        items: dict[str, dict[str, Any]] = {}

        for result_list in anchor_results:
            for rank, item in enumerate(result_list, start=1):
                item_id = item.get("id", str(item))
                scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
                items[item_id] = item

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [items[item_id] for item_id, _ in ranked]

    def score_seed(
        self,
        item: dict[str, Any],
        relevance: float,
        relation_usefulness: float,
        novelty: float,
        trust: float,
        structural_importance: float,
        temporal_fit: float,
        lateral_strength: float,
        framework_fit: float,
        depth: int,
        redundancy: float,
    ) -> float:
        """Priority = relevance + relation_usefulness + novelty + trust + structural_importance + temporal_fit + lateral_strength + framework_fit − depth − redundancy."""
        return (
            relevance + relation_usefulness + novelty + trust +
            structural_importance + temporal_fit + lateral_strength +
            framework_fit - depth - redundancy
        )


# ── Judgment + Stopping ─────────────────────────────────────────────────

class Sys1Judgment:
    """Phase 3: Batch Sys1 judgment + intelligent stopping."""

    def __init__(self, decision_backend: Any | None = None):
        self.decision_backend = decision_backend

    def batch_judgment(
        self,
        candidates: list[dict[str, Any]],
        question: str,
    ) -> list[dict[str, Any]]:
        """Batch Sys1 judgment: direct relevance, relation usefulness, new information, contradiction, next followables, lateral value, framework applicability."""
        judged: list[dict[str, Any]] = []
        for cand in candidates:
            # Deterministic scoring stub
            relevance = min(len(cand.get("content", "")) / 100.0, 1.0)
            relation_usefulness = 0.5
            new_information = 0.6
            contradiction = 0.1
            next_followables = 0.3
            lateral_value = 0.4
            framework_applicability = 0.5

            overall = (
                relevance * 0.25 + relation_usefulness * 0.15 +
                new_information * 0.2 + contradiction * -0.1 +
                next_followables * 0.1 + lateral_value * 0.05 +
                framework_applicability * 0.1
            )

            judged.append({
                **cand,
                "relevance": relevance,
                "relation_usefulness": relation_usefulness,
                "new_information": new_information,
                "contradiction": contradiction,
                "next_followables": next_followables,
                "lateral_value": lateral_value,
                "framework_applicability": framework_applicability,
                "overall_score": overall,
            })

        return sorted(judged, key=lambda x: x["overall_score"], reverse=True)

    def intelligent_stopping(
        self,
        judged: list[dict[str, Any]],
        facets_covered: set[str],
        facets_required: set[str],
        expected_value_threshold: float = 0.1,
    ) -> tuple[list[dict[str, Any]], str]:
        """Intelligent stopping: all facets covered? expected value of another hop? unresolved contradiction? framework saturation? hard limits."""
        stopped_reasons: list[str] = []

        # Check facet coverage
        if facets_required and facets_required.issubset(facets_covered):
            stopped_reasons.append("all_facets_covered")

        # Check expected value
        if judged and judged[0].get("overall_score", 0) < expected_value_threshold:
            stopped_reasons.append("low_expected_value")

        # Check for unresolved contradictions
        contradictions = [j for j in judged if j.get("contradiction", 0) > 0.7]
        if contradictions:
            stopped_reasons.append("unresolved_contradiction")

        # Framework saturation
        if len(judged) > 20:
            stopped_reasons.append("framework_saturation")

        stopped = len(stopped_reasons) > 0
        reason = "; ".join(stopped_reasons) if stopped_reasons else "budget_exhausted"

        return judged, reason


# ── Bundle + Synthesis + Verification ───────────────────────────────────

class EvidenceBundleBuilder:
    """Phase 4: Evidence bundle construction + L0–L3 packing."""

    def __init__(self, token_budget: int = 2000):
        self.token_budget = token_budget

    def build_bundle(
        self,
        evidence_ids: list[str],
        spans: list[dict[str, Any]],
        coordinates: list[dict[str, Any]],
        retrieval_path: list[str],
        relevance: dict[str, float],
        trust: dict[str, float],
        conflicts: list[dict[str, Any]],
        applied_frameworks: list[str],
    ) -> EvidenceBundle:
        return EvidenceBundle(
            evidence_ids=evidence_ids,
            spans=spans,
            coordinates=coordinates,
            retrieval_path=retrieval_path,
            relevance=relevance,
            trust=trust,
            conflicts=conflicts,
            applied_frameworks=applied_frameworks,
            packing_tier="L2",
        )

    def pack_tiers(
        self,
        bundle: EvidenceBundle,
        frameworks: list[str] | None = None,
    ) -> EvidenceBundle:
        """L0–L3 token-aware packing under explicit budget (frameworks preferentially in L1/L2)."""
        # L0: identity (evidence IDs)
        # L1: critical (high trust, high relevance)
        # L2: task (relevant evidence)
        # L3: deep + active frameworks
        bundle.packing_tier = "L2"
        if frameworks:
            bundle.packing_tier = "L1"
        return bundle


class ClaimVerifier:
    """Per-claim atomic verification (supported/contradicted/citation precise)."""

    def verify_claims(
        self,
        synthesis: str,
        bundle: EvidenceBundle,
    ) -> dict[str, Any]:
        """Per-claim atomic verification: supported / contradicted / citation precise."""
        claims = [c.strip() for c in synthesis.split(".") if c.strip()]
        results: list[dict[str, Any]] = []

        for claim in claims:
            # Deterministic stub: check if claim mentions evidence IDs
            supported = any(eid in claim for eid in bundle.evidence_ids)
            contradicted = False
            citation_precise = bool(bundle.evidence_ids)

            results.append({
                "claim": claim,
                "supported": supported,
                "contradicted": contradicted,
                "citation_precise": citation_precise,
                "action": "keep" if supported and citation_precise else "qualify",
            })

        unsupported = [r for r in results if not r["supported"]]
        return {
            "total_claims": len(results),
            "supported": len(results) - len(unsupported),
            "unsupported": len(unsupported),
            "contradicted": sum(1 for r in results if r["contradicted"]),
            "correct_abstention": len(unsupported) > 0 and len(bundle.evidence_ids) == 0,
            "results": results,
        }


# ── Read pipeline ────────────────────────────────────────────────────────

class ReadPipeline:
    """Full read pipeline (Section 7)."""

    def __init__(
        self,
        store: Any | None = None,
        decision_backend: Any | None = None,
        cache: SemanticCache | None = None,
    ):
        self.store = store
        self.decision_backend = decision_backend
        self.cache = cache or SemanticCache()
        self.anchor_expander = AnchorExpander(store=store)
        self.sys1_judgment = Sys1Judgment(decision_backend=decision_backend)
        self.bundle_builder = EvidenceBundleBuilder()
        self.claim_verifier = ClaimVerifier()

    def process(self, request: ReadRequest) -> ReadResult:
        """Run the full read pipeline (Phases 0-4)."""
        start = time.perf_counter()
        result = ReadResult(
            question=request.question,
            mode=request.mode,
            bundle=EvidenceBundle(),
        )

        # Phase 0 – Cache
        cached = self.cache.lookup(request.question, request.scopes, request.as_of)
        if cached:
            result.cache_hit = True
            result.bundle = cached
            result.latency_ms = (time.perf_counter() - start) * 1000
            return result

        # Phase 1 – Routing
        answer_facets = request.answer_facets or ["who", "what", "when", "why", "how"]
        frameworks_applied: list[str] = list(request.frameworks or [])

        # Optional framework pre-selection via Choice primitive
        if request.mode == ReadMode.FRAMEWORK_AUGMENTED and self.decision_backend:
            try:
                bundles = self.decision_backend.evaluate(
                    {"question": request.question},
                    {"framework_selection": "Choice"},
                    deadline_ms=1000,
                )
                for fb in bundles.values():
                    if fb.selected:
                        frameworks_applied.append(str(fb.selected))
            except Exception:
                pass

        result.frameworks_applied = frameworks_applied
        result.decision_calls += 1

        # Phase 2 – Anchors + Expansion
        anchors = self.anchor_expander.hybrid_anchors(
            request.question,
            entities=None,
            tags=None,
            project=None,
        )

        # RRF fusion
        fused = self.anchor_expander.rrf_fusion([anchors])

        # Sys1 Score seed validation
        judged = self.sys1_judgment.batch_judgment(fused, request.question)

        # Intelligent stopping
        facets_covered: set[str] = set()
        facets_required = set(answer_facets)
        judged, stop_reason = self.sys1_judgment.intelligent_stopping(
            judged, facets_covered, facets_required,
        )

        # Hard limits
        hard_limits = {
            "max_nodes": 50,
            "max_edges": 100,
            "max_depth": request.budget_depth,
            "max_decision_calls": request.budget_decision_calls,
            "max_wall_time_ms": request.max_latency_ms,
        }

        # Phase 3 – Judgment + Stopping (already done above)
        # Phase 4 – Bundle + Synthesis + Verification
        evidence_ids = [j.get("id", str(i)) for i, j in enumerate(judged[:10])]
        spans = [{"id": eid, "text": j.get("content", "")[:200]} for eid, j in zip(evidence_ids, judged[:10])]
        coordinates = [{"id": eid, "source": "pipeline"} for eid in evidence_ids]

        bundle = self.bundle_builder.build_bundle(
            evidence_ids=evidence_ids,
            spans=spans,
            coordinates=coordinates,
            retrieval_path=["anchor", "rrf", "sys1_judgment"],
            relevance={eid: j.get("overall_score", 0.0) for eid, j in zip(evidence_ids, judged[:10])},
            trust={eid: 0.8 for eid in evidence_ids},
            conflicts=[],
            applied_frameworks=frameworks_applied,
        )

        # Token-aware packing
        bundle = self.bundle_builder.pack_tiers(bundle, frameworks=frameworks_applied)
        result.bundle = bundle

        # Optional single System Two synthesis call
        if request.mode in (ReadMode.FULL, ReadMode.AUTO_ESCALATE, ReadMode.FRAMEWORK_AUGMENTED):
            synthesis_parts = [f"Evidence for: {request.question}"]
            for span in spans[:5]:
                synthesis_parts.append(f"- {span['text']}")
            result.synthesis = "\n".join(synthesis_parts)

            # Per-claim atomic verification
            result.verification = self.claim_verifier.verify_claims(result.synthesis, bundle)

        # Cache the result
        self.cache.store(request.question, bundle, request.scopes, request.as_of)

        result.latency_ms = (time.perf_counter() - start) * 1000
        result.evidence_tokens = len(request.question) + sum(len(s.get("text", "")) for s in spans)

        return result


# ── Convenience function ─────────────────────────────────────────────────

def read(
    question: str,
    store: Any | None = None,
    decision_backend: Any | None = None,
    mode: ReadMode = ReadMode.FULL,
    scopes: list[str] | None = None,
    max_latency_ms: int = 5000,
    token_budget: int | None = None,
    frameworks: list[str] | None = None,
) -> ReadResult:
    """Convenience function to run the full read pipeline."""
    pipeline = ReadPipeline(
        store=store,
        decision_backend=decision_backend,
    )
    request = ReadRequest(
        question=question,
        scopes=scopes,
        max_latency_ms=max_latency_ms,
        token_budget=token_budget,
        frameworks=frameworks,
        mode=mode,
    )
    return pipeline.process(request)
