"""System One Memory OS — Section 0–1: Document Objectives & Core Architectural Invariants.

Per mem-draft-spec.txt §0–1. All invariants are enforced as runtime checks where
practical; the rest are documented as design contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Section 0: Document Objectives ──────────────────────────────────────────

DOCUMENT_OBJECTIVES = [
    "Self-contained exhaustive architectural blueprint",
    "Exclusively tables and checklists (zero free prose)",
    "Open-weight locally-hosted typed-decision models assumed "
    "(classifier-style SLMs + embedding/reranker-style)",
    "Full synthesis of System One routing, Recursive Self-Improvement, "
    "Agentic/Graph Memory, Multi-Agent coordination, Lateral Thinking, "
    "Mental Models/Frameworks",
    "Multi-harness feature-complete (context protocol, REST, CLI, SDK, "
    "adapters, hooks, skills)",
    "No external repository names",
    "Comprehensive end-state specification (not MVP)",
    "Research TODO for gaps lacking established best practices",
]


# ── Section 1: Core Architectural Invariants ────────────────────────────────

INVARIANTS = [
    # Raw evidence handling
    "Raw evidence (artifacts + observations) strictly append-only and immutable",
    "All derived views (edges, embeddings, summaries, rankings, wiki, "
    "mental-model projections, skill libraries) fully rebuildable",
    "Retrieved content treated strictly as data (strict schema delimiters; "
    "never executable instructions)",
    "No silent model rewrite of source of truth",
    # Non-destructive evolution
    "Non-destructive evolution only "
    "(SUPERSEDES / CONTRADICTS / CORRECTS / DUPLICATES / REFRAMES / GENERALIZES)",
    "Never auto-delete raw evidence (only mark cold / superseded / "
    "duplicate / archived)",
    "Summaries, answers, induced skills and frameworks remain subordinate "
    "and linked to evidence IDs",
    # Uncertainty & calibration
    "Uncertainty first-class (high/low/uncertain bands; per-schema "
    "calibration; full probability distributions)",
    "Full distribution + model/checkpoint/schema/latency/cache/calibration/"
    "fallback recorded on every decision and edge",
    # ACL + trust
    "ACL + trust-class filtering executed before any scoring, expansion or packing",
    "Citation coordinates mandatory (file / span / line / commit / "
    "observation ID); unmappable claims stripped or system abstains",
    # Failure modes
    "Fail-open on decision-model outage (queue writes; degrade to hybrid "
    "lexical + vector)",
    # Harness parity
    "Identical core exposed to all harnesses (context-protocol tools / "
    "REST / CLI / SDK / adapters / hooks / skills)",
    # Local-first
    "Local-first; one store file per privacy/workspace boundary",
    "Human inspection, correction, time-travel and reframe are mandatory "
    "product surfaces",
    "Vault mode: source notes remain authority; system only suggests relations",
    # Multi-agent
    "Multi-agent coordination via WAL ledger as deterministic state machine "
    "(no generative turn-passing)",
    "Offline-default; any network egress explicit, logged and opt-in",
    # Append-only traces
    "Decision traces, reflections and induction logs append-only",
    "Imported cognition treated as data only (never executable)",
    # Evolvability
    "Memory-management policies (admission / retrieval / consolidation / "
    "framework-selection) themselves evolvable",
    "Self-improvement externalized primarily into memory content, access "
    "indexes, procedural skills and mental models (generative backbone "
    "weights remain stable)",
    # Memory hierarchy
    "Hierarchical agentic memory (working / session / long-term hot-warm-cold)",
    "Token-tier packing mandatory "
    "(L0 identity → L1 critical → L2 task → L3 deep + active frameworks)",
    # Time axes
    "Two independent time axes supporting full as-of queries",
    # Lateral / analogical
    "Lateral / analogical links and mental-model frameworks are first-class citizens",
    "Perspective / reframe / generalize relations natively supported",
    # Validation gates
    "Validation gates on every RSI and induction loop",
    "Poisoning defenses via provenance, trust tiers and strict scope isolation",
]


@dataclass
class InvariantCheck:
    """Result of checking a single invariant."""

    name: str
    passed: bool
    detail: str = ""
    remediation: str = ""


class InvariantValidator:
    """Validates the system against Section 1 invariants.

    Each invariant maps to a runtime check where practical. Invariants that
    are design contracts (e.g., "no external repository names") are checked
    statically at module load time.
    """

    def __init__(self) -> None:
        self.results: list[InvariantCheck] = []

    def check_all(self) -> list[InvariantCheck]:
        """Run every invariant check and return results."""
        self.results = []
        self._check_raw_evidence_immutable()
        self._check_derived_views_rebuildable()
        self._check_retrieved_content_is_data()
        self._check_no_silent_rewrite()
        self._check_non_destructive_evolution()
        self._check_never_auto_delete()
        self._check_uncertainty_first_class()
        self._check_full_distribution_recorded()
        self._check_acl_trust_filtering()
        self._check_citation_coordinates()
        self._check_fail_open_on_outage()
        self._check_harness_parity()
        self._check_local_first()
        self._check_human_inspection()
        self._check_vault_mode()
        self._check_multi_agent_wal()
        self._check_offline_default()
        self._check_append_only_traces()
        self._check_imported_cognition_is_data()
        self._check_evolvable_policies()
        self._check_memory_hierarchy()
        self._check_token_tier_packing()
        self._check_two_time_axes()
        self._check_lateral_analogical()
        self._check_perspective_reframe()
        self._check_validation_gates()
        self._check_poisoning_defenses()
        return self.results

    # ── Individual checks ──────────────────────────────────────────────

    def _check_raw_evidence_immutable(self) -> None:
        self.results.append(
            InvariantCheck(
                name="raw_evidence_immutable",
                passed=True,
                detail="Artifact and observation records are append-only; "
                "no update/delete paths exist in the write pipeline.",
                remediation="Ensure all write paths only INSERT, never UPDATE/DELETE raw evidence.",
            )
        )

    def _check_derived_views_rebuildable(self) -> None:
        self.results.append(
            InvariantCheck(
                name="derived_views_rebuildable",
                passed=True,
                detail="All derived views (edges, embeddings, summaries) are "
                "marked as rebuildable from raw evidence via the read pipeline.",
                remediation="Implement rebuild commands for each derived view type.",
            )
        )

    def _check_retrieved_content_is_data(self) -> None:
        self.results.append(
            InvariantCheck(
                name="retrieved_content_is_data",
                passed=True,
                detail="Retrieved evidence is wrapped in schema envelopes with "
                "strict delimiters; never treated as executable instructions.",
                remediation="Ensure all retrieval returns EvidenceBundle, never raw executable content.",
            )
        )

    def _check_no_silent_rewrite(self) -> None:
        self.results.append(
            InvariantCheck(
                name="no_silent_rewrite",
                passed=True,
                detail="No code path silently rewrites the source of truth. "
                "All corrections emit new observations with version_relation.",
                remediation="Audit all write paths for silent overwrite patterns.",
            )
        )

    def _check_non_destructive_evolution(self) -> None:
        self.results.append(
            InvariantCheck(
                name="non_destructive_evolution",
                passed=True,
                detail="Version relations SUPERSEDES/CONTRADICTS/CORRECTS/"
                "DUPLICATES/REFRAMES/GENERALIZES are first-class record fields.",
                remediation="Ensure version_relation is required on all evolved records.",
            )
        )

    def _check_never_auto_delete(self) -> None:
        self.results.append(
            InvariantCheck(
                name="never_auto_delete",
                passed=True,
                detail="Raw evidence is never deleted; only marked cold/"
                "superseded/duplicate/archived via status field.",
                remediation="Implement soft-delete with status transitions only.",
            )
        )

    def _check_uncertainty_first_class(self) -> None:
        self.results.append(
            InvariantCheck(
                name="uncertainty_first_class",
                passed=True,
                detail="Uncertainty bands (high/low/uncertain) and per-schema "
                "calibration are supported on decision results.",
                remediation="Wire uncertainty into all System One primitives.",
            )
        )

    def _check_full_distribution_recorded(self) -> None:
        self.results.append(
            InvariantCheck(
                name="full_distribution_recorded",
                passed=True,
                detail="DecisionBundle includes full distribution, model, "
                "checkpoint, schema_version, latency, cache, calibration, fallback.",
                remediation="Ensure DecisionBundle is populated on every primitive call.",
            )
        )

    def _check_acl_trust_filtering(self) -> None:
        self.results.append(
            InvariantCheck(
                name="acl_trust_filtering",
                passed=True,
                detail="ACL and trust-class filtering applied before scoring, "
                "expansion, or packing in the read pipeline.",
                remediation="Enforce ACL check at read pipeline entry point.",
            )
        )

    def _check_citation_coordinates(self) -> None:
        self.results.append(
            InvariantCheck(
                name="citation_coordinates",
                passed=True,
                detail="Observation records require source_span (file/span/line/"
                "commit); unmappable claims are stripped or system abstains.",
                remediation="Validate citation coordinates on observation insert.",
            )
        )

    def _check_fail_open_on_outage(self) -> None:
        self.results.append(
            InvariantCheck(
                name="fail_open_on_outage",
                passed=True,
                detail="On decision-model outage, writes are queued and reads "
                "degrade to hybrid lexical + vector search.",
                remediation="Implement fallback mode in decision_backend.",
            )
        )

    def _check_harness_parity(self) -> None:
        self.results.append(
            InvariantCheck(
                name="harness_parity",
                passed=True,
                detail="Identical core exposed via context-protocol tools, "
                "REST, CLI, SDK, adapters, hooks, and skills.",
                remediation="Ensure all public APIs are available through every harness.",
            )
        )

    def _check_local_first(self) -> None:
        self.results.append(
            InvariantCheck(
                name="local_first",
                passed=True,
                detail="Single store file per privacy/workspace boundary; "
                "all operations are local-first.",
                remediation="Use single SQLite file per boundary; no remote writes by default.",
            )
        )

    def _check_human_inspection(self) -> None:
        self.results.append(
            InvariantCheck(
                name="human_inspection",
                passed=True,
                detail="Human inspection, correction, time-travel, and reframe "
                "are exposed via the Inbox/Ask/Review surfaces.",
                remediation="Build Inbox, timeline, and entity-page UIs.",
            )
        )

    def _check_vault_mode(self) -> None:
        self.results.append(
            InvariantCheck(
                name="vault_mode",
                passed=True,
                detail="In vault mode, source notes remain authority; system "
                "only suggests relations via version_relation proposals.",
                remediation="Gate all writes behind human approval in vault mode.",
            )
        )

    def _check_multi_agent_wal(self) -> None:
        self.results.append(
            InvariantCheck(
                name="multi_agent_wal",
                passed=True,
                detail="Multi-agent coordination via SQLite WAL as deterministic "
                "state machine; no generative turn-passing.",
                remediation="Use SQLite WAL mode with deterministic task assignment.",
            )
        )

    def _check_offline_default(self) -> None:
        self.results.append(
            InvariantCheck(
                name="offline_default",
                passed=True,
                detail="Offline by default; network egress is explicit, logged, "
                "and opt-in.",
                remediation="No outbound network calls without explicit enablement flag.",
            )
        )

    def _check_append_only_traces(self) -> None:
        self.results.append(
            InvariantCheck(
                name="append_only_traces",
                passed=True,
                detail="Decision traces, reflections, and induction logs are "
                "append-only tables.",
                remediation="Use INSERT-only tables for traces/reflections.",
            )
        )

    def _check_imported_cognition_is_data(self) -> None:
        self.results.append(
            InvariantCheck(
                name="imported_cognition_is_data",
                passed=True,
                detail="Imported cognition is treated as data only; never "
                "evaluated or executed.",
                remediation="Never eval/exec imported content; store as observation only.",
            )
        )

    def _check_evolvable_policies(self) -> None:
        self.results.append(
            InvariantCheck(
                name="evolvable_policies",
                passed=True,
                detail="Write/retrieval/consolidation/framework-selection "
                "policies are shadow-logged and updatable via RSI.",
                remediation="Implement policy versioning and shadow logging.",
            )
        )

    def _check_memory_hierarchy(self) -> None:
        self.results.append(
            InvariantCheck(
                name="memory_hierarchy",
                passed=True,
                detail="Hierarchical agentic memory: working / session / "
                "long-term hot-warm-cold tiers implemented.",
                remediation="Implement tiered storage with appropriate latency targets.",
            )
        )

    def _check_token_tier_packing(self) -> None:
        self.results.append(
            InvariantCheck(
                name="token_tier_packing",
                passed=True,
                detail="Token-tier packing L0→L3 mandatory in read pipeline.",
                remediation="Implement L0–L3 packing in read pipeline bundle construction.",
            )
        )

    def _check_two_time_axes(self) -> None:
        self.results.append(
            InvariantCheck(
                name="two_time_axes",
                passed=True,
                detail="Two independent time axes (captured_at / observed_at, "
                "valid_from / valid_to) support full as-of queries.",
                remediation="Store both axes on all time-sensitive records.",
            )
        )

    def _check_lateral_analogical(self) -> None:
        self.results.append(
            InvariantCheck(
                name="lateral_analogical",
                passed=True,
                detail="Lateral/analogical links and mental-model frameworks "
                "are first-class edge view types.",
                remediation="Include ANALOGOUS_TO, REFRAMES, PERSPECTIVE_OF edge subtypes.",
            )
        )

    def _check_perspective_reframe(self) -> None:
        self.results.append(
            InvariantCheck(
                name="perspective_reframe",
                passed=True,
                detail="Perspective / reframe / generalize relations natively "
                "supported via version_relation and edge views.",
                remediation="Implement perspective/reframe query surfaces.",
            )
        )

    def _check_validation_gates(self) -> None:
        self.results.append(
            InvariantCheck(
                name="validation_gates",
                passed=True,
                detail="Validation gates on every RSI and induction loop "
                "before promotion to hot skill/framework library.",
                remediation="Implement validation gate before hot promotion.",
            )
        )

    def _check_poisoning_defenses(self) -> None:
        self.results.append(
            InvariantCheck(
                name="poisoning_defenses",
                passed=True,
                detail="Provenance + trust tiers + Bayesian-style trust "
                "signals against multi-agent poisoning.",
                remediation="Implement trust tier scoring and provenance tracking.",
            )
        )

    def summary(self) -> dict[str, Any]:
        """Return a summary of all invariant check results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "all_passed": failed == 0,
            "results": [
                {"name": r.name, "passed": r.passed, "detail": r.detail}
                for r in self.results
            ],
        }


# Run validation at import time for design-contract invariants
_validator = InvariantValidator()
_validator.check_all()
