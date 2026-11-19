"""Borg — Phase 2: S6 Tacit Agent.

Per mem-draft-spec.txt §4 (Pipeline S6):
S6 Tacit — Judgment and nuance.

Captures tacit judgment calls, analyzes nuance in situations, routes
decisions based on context, and preserves context for future reuse.

Sub-prompts are loaded from separate template files in prompts/ for modularity.

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json


# ── Sub-prompt loading ───────────────────────────────────────────────────
_cli_dir = Path(__file__).resolve().parent
_prompts_dir = _cli_dir / "prompts"


def _load_prompt_file(name: str) -> str:
    path = _prompts_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


S6_TACIT_CAPTURE_PROMPT = _load_prompt_file("s6_tacit_capture_prompt")
S6_NUANCE_ANALYZE_PROMPT = _load_prompt_file("s6_nuance_analyze_prompt")
S6_JUDGMENT_ROUTE_PROMPT = _load_prompt_file("s6_judgment_route_prompt")
S6_CONTEXT_PRESERVE_PROMPT = _load_prompt_file("s6_context_preserve_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Types ────────────────────────────────────────────────────────────────

@dataclass
class Judgment:
    """A captured tacit judgment call."""

    id: str
    situation: str
    decision: str
    reasoning: str
    context_factors: list[str] = field(default_factory=list)
    outcome: str | None = None
    confidence: float = 0.0
    tags: list[str] = field(default_factory=list)
    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "situation": self.situation,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "context_factors": list(self.context_factors),
            "outcome": self.outcome,
            "confidence": self.confidence,
            "tags": list(self.tags),
            "captured_at": self.captured_at,
        }


@dataclass
class NuanceAnalysis:
    """Analysis of nuance in a situation."""

    unique_aspects: list[str] = field(default_factory=list)
    nuance_factors: list[str] = field(default_factory=list)
    decisive_factors: list[str] = field(default_factory=list)
    peripheral_factors: list[str] = field(default_factory=list)
    past_decision_applicability: str = "not_applicable"
    nuance_complexity: str = "moderate"
    blind_spots: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "unique_aspects": list(self.unique_aspects),
            "nuance_factors": list(self.nuance_factors),
            "decisive_factors": list(self.decisive_factors),
            "peripheral_factors": list(self.peripheral_factors),
            "past_decision_applicability": self.past_decision_applicability,
            "nuance_complexity": self.nuance_complexity,
            "blind_spots": list(self.blind_spots),
            "missing_information": list(self.missing_information),
        }


@dataclass
class Routing:
    """Decision routing recommendation."""

    decision_owner: str = "individual"
    deliberation_process: str = "quick"
    consulted: list[str] = field(default_factory=list)
    informed: list[str] = field(default_factory=list)
    approach: str = "hybrid"
    complexity_assessment: str = "medium"
    escalation_triggers: list[str] = field(default_factory=list)
    reversibility_check: str = "partially"
    time_sensitivity: str = "moderate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_owner": self.decision_owner,
            "deliberation_process": self.deliberation_process,
            "consulted": list(self.consulted),
            "informed": list(self.informed),
            "approach": self.approach,
            "complexity_assessment": self.complexity_assessment,
            "escalation_triggers": list(self.escalation_triggers),
            "reversibility_check": self.reversibility_check,
            "time_sensitivity": self.time_sensitivity,
        }


@dataclass
class ContextPreservation:
    """Preserved context for future similar decisions."""

    judgment_id: str
    situation_key: str
    applicability_scope: str = "moderate"
    review_triggers: list[str] = field(default_factory=list)
    related_judgments: list[str] = field(default_factory=list)
    preserved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    lookup_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "judgment_id": self.judgment_id,
            "situation_key": self.situation_key,
            "applicability_scope": self.applicability_scope,
            "review_triggers": list(self.review_triggers),
            "related_judgments": list(self.related_judgments),
            "preserved_at": self.preserved_at,
            "lookup_tags": list(self.lookup_tags),
        }


# ── Helper functions ─────────────────────────────────────────────────────

def _judgment_id(situation: str) -> str:
    """Generate a deterministic judgment ID."""
    h = hashlib.sha256(situation.encode()).hexdigest()[:12]
    return f"t:{h}"


def _assess_complexity(
    impact_level: str,
    reversibility: str,
    time_pressure: str,
) -> str:
    """Assess decision complexity."""
    score = 0
    impact_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    reversibility_scores = {"fully": 1, "partially": 2, "not": 3}
    time_scores = {"plenty": 1, "moderate": 2, "urgent": 3, "immediate": 4}

    score += impact_scores.get(impact_level, 2)
    score += reversibility_scores.get(reversibility, 2)
    score += time_scores.get(time_pressure, 2)

    if score <= 5:
        return "low"
    elif score <= 8:
        return "medium"
    elif score <= 10:
        return "high"
    else:
        return "critical"


def _route_owner(complexity: str, impact_level: str) -> str:
    """Determine who should own the decision."""
    if complexity == "critical" or impact_level == "critical":
        return "escalate"
    if complexity == "high" or impact_level == "high":
        return "team"
    return "individual"


def _route_process(complexity: str, time_sensitivity: str) -> str:
    """Determine deliberation process."""
    if complexity in ("high", "critical") and time_sensitivity != "immediate":
        return "formal"
    if complexity == "medium":
        return "structured"
    if time_sensitivity in ("urgent", "immediate"):
        return "quick"
    return "consensus"


# ── Step 1: Capture Judgment ─────────────────────────────────────────────

def step_capture_judgment(
    situation: str,
    decision: str,
    reasoning: str,
    context_factors: list[str] | None = None,
    outcome: str | None = None,
    confidence: float = 0.5,
    tags: list[str] | None = None,
) -> tuple[Judgment, list[str]]:
    """Capture a tacit judgment call.

    Returns (judgment, errors).
    """
    errors: list[str] = []
    context_factors = context_factors or []
    tags = tags or []

    if not situation or not situation.strip():
        errors.append("Situation cannot be empty")
        return Judgment(id="", situation="", decision="", reasoning=""), errors

    if not decision or not decision.strip():
        errors.append("Decision cannot be empty")
        return Judgment(id="", situation="", decision="", reasoning=""), errors

    if not 0.0 <= confidence <= 1.0:
        errors.append("Confidence must be between 0.0 and 1.0")
        confidence = 0.5

    judgment = Judgment(
        id=_judgment_id(situation),
        situation=situation.strip(),
        decision=decision.strip(),
        reasoning=reasoning.strip(),
        context_factors=list(context_factors),
        outcome=outcome,
        confidence=confidence,
        tags=list(tags),
    )

    return judgment, errors


# ── Step 2: Analyze Nuance ───────────────────────────────────────────────

def step_analyze_nuance(
    situation: str,
    similar_decisions: list[str] | None = None,
    context: str | None = None,
) -> tuple[NuanceAnalysis, list[str]]:
    """Analyze nuance in a situation.

    Returns (analysis, errors).
    """
    errors: list[str] = []
    similar_decisions = similar_decisions or []
    context = context or ""

    lower = situation.lower()
    context_lower = context.lower()

    # Identify unique aspects
    unique_aspects: list[str] = []
    nuance_indicators = [
        "but", "however", "although", "except", "unless", "depending",
        "specific", "particular", "unique", "special", "unusual",
    ]
    for indicator in nuance_indicators:
        if indicator in lower:
            unique_aspects.append(f"Contains nuance indicator: '{indicator}'")

    if not unique_aspects:
        unique_aspects.append("No obvious nuance indicators detected")

    # Nuance factors
    nuance_factors = [
        "Context-dependent reasoning",
        "Implicit assumptions",
        "Unstated constraints",
    ]

    # Decisive vs peripheral
    decisive_factors = ["Impact level", "Reversibility", "Time pressure"]
    peripheral_factors = ["Personal preference", "Historical precedent"]

    # Past decision applicability
    if similar_decisions:
        applicability = "adapted"
    else:
        applicability = "not_applicable"

    # Nuance complexity
    if len(unique_aspects) > 3 or len(nuance_factors) > 3:
        complexity = "complex"
    elif len(unique_aspects) > 1:
        complexity = "moderate"
    else:
        complexity = "simple"

    # Blind spots
    blind_spots = [
        "Potential confirmation bias",
        "Possible overlooked stakeholders",
    ]

    # Missing information
    missing_information = [
        "Quantitative impact data",
        "Stakeholder input",
    ]

    analysis = NuanceAnalysis(
        unique_aspects=unique_aspects,
        nuance_factors=nuance_factors,
        decisive_factors=decisive_factors,
        peripheral_factors=peripheral_factors,
        past_decision_applicability=applicability,
        nuance_complexity=complexity,
        blind_spots=blind_spots,
        missing_information=missing_information,
    )

    return analysis, errors


# ── Step 3: Route Judgment ───────────────────────────────────────────────

def step_route_judgment(
    situation: str,
    decision_type: str,
    impact_level: str,
    reversibility: str,
    time_pressure: str,
    available_expertise: list[str] | None = None,
) -> tuple[Routing, list[str]]:
    """Route a decision based on context.

    Returns (routing, errors).
    """
    errors: list[str] = []
    available_expertise = available_expertise or []

    complexity = _assess_complexity(impact_level, reversibility, time_pressure)
    owner = _route_owner(complexity, impact_level)
    process = _route_process(complexity, time_pressure)

    # Consulted roles
    consulted: list[str] = []
    if available_expertise:
        consulted.extend(available_expertise[:3])
    if complexity in ("high", "critical"):
        consulted.append("domain_expert")
    if impact_level in ("high", "critical"):
        consulted.append("stakeholder_representative")

    # Informed roles
    informed: list[str] = ["team_lead", "documentation_keeper"]

    # Approach
    if complexity == "low":
        approach = "intuition"
    elif complexity == "critical":
        approach = "analysis"
    else:
        approach = "hybrid"

    # Escalation triggers
    escalation_triggers = [
        "Impact exceeds predefined threshold",
        "Decision affects multiple teams",
        "Legal or compliance implications",
    ]

    # Reversibility check
    reversibility_check = reversibility

    routing = Routing(
        decision_owner=owner,
        deliberation_process=process,
        consulted=list(dict.fromkeys(consulted)),
        informed=list(dict.fromkeys(informed)),
        approach=approach,
        complexity_assessment=complexity,
        escalation_triggers=escalation_triggers,
        reversibility_check=reversibility_check,
        time_sensitivity=time_pressure,
    )

    return routing, errors


# ── Step 4: Preserve Context ─────────────────────────────────────────────

def step_preserve_context(
    judgment_id: str,
    situation_key: str,
    applicability_scope: str = "moderate",
    review_triggers: list[str] | None = None,
    related_judgments: list[str] | None = None,
) -> tuple[ContextPreservation, list[str]]:
    """Preserve context for future similar decisions.

    Returns (preservation, errors).
    """
    errors: list[str] = []
    review_triggers = review_triggers or []
    related_judgments = related_judgments or []

    if not situation_key or not situation_key.strip():
        errors.append("Situation key cannot be empty")
        return ContextPreservation(
            judgment_id=judgment_id,
            situation_key="",
        ), errors

    lookup_tags = [situation_key.lower().replace(" ", "-")]
    if applicability_scope:
        lookup_tags.append(f"scope:{applicability_scope}")

    preservation = ContextPreservation(
        judgment_id=judgment_id,
        situation_key=situation_key.strip(),
        applicability_scope=applicability_scope,
        review_triggers=list(review_triggers),
        related_judgments=list(related_judgments),
        lookup_tags=lookup_tags,
    )

    return preservation, errors


# ── S6 Tacit Agent ───────────────────────────────────────────────────────

class S6Tacit:
    """S6 Tacit agent — Judgment and nuance.

    Captures tacit judgment calls, analyzes nuance, routes decisions,
    and preserves context for future reuse.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._judgments: dict[str, Judgment] = {}
        self._analyses: dict[str, NuanceAnalysis] = {}
        self._routings: dict[str, Routing] = {}
        self._preservations: dict[str, ContextPreservation] = {}

    # ── Capture ─────────────────────────────────────────────────────

    def capture_judgment(
        self,
        situation: str,
        decision: str,
        reasoning: str,
        context_factors: list[str] | None = None,
        outcome: str | None = None,
        confidence: float = 0.5,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Capture a tacit judgment call."""
        judgment, errors = step_capture_judgment(
            situation, decision, reasoning, context_factors, outcome, confidence, tags
        )
        if judgment.id:
            self._judgments[judgment.id] = judgment
        return {
            "judgment": judgment.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Analyze Nuance ──────────────────────────────────────────────

    def analyze_nuance(
        self,
        situation: str,
        similar_decisions: list[str] | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Analyze nuance in a situation."""
        analysis, errors = step_analyze_nuance(situation, similar_decisions, context)
        return {
            "nuance_analysis": analysis.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Route ───────────────────────────────────────────────────────

    def route_judgment(
        self,
        situation: str,
        decision_type: str,
        impact_level: str,
        reversibility: str,
        time_pressure: str,
        available_expertise: list[str] | None = None,
    ) -> dict[str, Any]:
        """Route a decision based on context."""
        routing, errors = step_route_judgment(
            situation, decision_type, impact_level, reversibility, time_pressure, available_expertise
        )
        return {
            "routing": routing.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Preserve ────────────────────────────────────────────────────

    def preserve_context(
        self,
        judgment_id: str,
        situation_key: str,
        applicability_scope: str = "moderate",
        review_triggers: list[str] | None = None,
        related_judgments: list[str] | None = None,
    ) -> dict[str, Any]:
        """Preserve context for future similar decisions."""
        preservation, errors = step_preserve_context(
            judgment_id, situation_key, applicability_scope, review_triggers, related_judgments
        )
        if preservation.judgment_id:
            self._preservations[preservation.situation_key] = preservation
        return {
            "context_preservation": preservation.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Tacit statistics."""
        return {
            "total_judgments": len(self._judgments),
            "total_analyses": len(self._analyses),
            "total_routings": len(self._routings),
            "total_preservations": len(self._preservations),
            "judgments_with_outcome": sum(
                1 for j in self._judgments.values() if j.outcome is not None
            ),
            "high_confidence_judgments": sum(
                1 for j in self._judgments.values() if j.confidence >= 0.8
            ),
        }

    # ── Persistence ────────────────────────────────────────────────

    def save_to_vault(self, apply: bool = False) -> str | None:
        """Save tacit data to vault as JSON (if --apply / vault configured)."""
        if not self.vault_path or not apply:
            return None

        dir_path = self.vault_path / "02-Areas" / "Skills"
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {
            "judgments": {jid: j.to_dict() for jid, j in self._judgments.items()},
            "analyses": {key: a.to_dict() for key, a in self._analyses.items()},
            "routings": {key: r.to_dict() for key, r in self._routings.items()},
            "preservations": {key: p.to_dict() for key, p in self._preservations.items()},
            "stats": self.stats(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        path = dir_path / "tacit-judgments.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def load_from_vault(self) -> bool:
        """Load tacit data from vault JSON file."""
        if not self.vault_path:
            return False

        path = self.vault_path / "02-Areas" / "Skills" / "tacit-judgments.json"
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for jid, jdata in data.get("judgments", {}).items():
                self._judgments[jid] = Judgment(**jdata)
            for key, adata in data.get("analyses", {}).items():
                self._analyses[key] = NuanceAnalysis(**adata)
            for key, rdata in data.get("routings", {}).items():
                self._routings[key] = Routing(**rdata)
            for key, pdata in data.get("preservations", {}).items():
                self._preservations[key] = ContextPreservation(**pdata)
            return True
        except (json.JSONDecodeError, TypeError, KeyError):
            return False


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S6 Tacit — Judgment and nuance",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")

    sub = parser.add_subparsers(dest="command")

    # capture
    p_capture = sub.add_parser("capture", help="Capture a tacit judgment call")
    p_capture.add_argument("--situation", required=True, help="Situation description")
    p_capture.add_argument("--decision", required=True, help="Decision made")
    p_capture.add_argument("--reasoning", required=True, help="Reasoning behind decision")
    p_capture.add_argument(
        "--context-factors", default="", help="Comma-separated context factors"
    )
    p_capture.add_argument("--outcome", default="", help="Outcome if known")
    p_capture.add_argument(
        "--confidence", type=float, default=0.5, help="Confidence level (0.0-1.0)"
    )
    p_capture.add_argument("--tags", default="", help="Comma-separated tags")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze nuance in a situation")
    p_analyze.add_argument("--situation", required=True, help="Situation description")
    p_analyze.add_argument(
        "--similar-decisions", default="", help="Comma-separated similar decisions"
    )
    p_analyze.add_argument("--context", default="", help="Additional context")

    # route
    p_route = sub.add_parser("route", help="Route a decision based on context")
    p_route.add_argument("--situation", required=True, help="Situation description")
    p_route.add_argument(
        "--decision-type", required=True, help="Type of decision"
    )
    p_route.add_argument(
        "--impact-level", required=True, help="Impact level (low/medium/high/critical)"
    )
    p_route.add_argument(
        "--reversibility", required=True, help="Reversibility (fully/partially/not)"
    )
    p_route.add_argument(
        "--time-pressure", required=True, help="Time pressure (plenty/moderate/urgent/immediate)"
    )
    p_route.add_argument(
        "--available-expertise", default="", help="Comma-separated expertise"
    )

    # preserve
    p_preserve = sub.add_parser(
        "preserve", help="Preserve context for future similar decisions"
    )
    p_preserve.add_argument("--judgment-id", required=True, help="Judgment ID")
    p_preserve.add_argument(
        "--situation-key", required=True, help="Key phrase for lookup"
    )
    p_preserve.add_argument(
        "--applicability-scope", default="moderate", help="Scope (narrow/moderate/broad)"
    )
    p_preserve.add_argument(
        "--review-triggers", default="", help="Comma-separated review triggers"
    )
    p_preserve.add_argument(
        "--related-judgments", default="", help="Comma-separated related judgment IDs"
    )

    # stats
    sub.add_parser("stats", help="Show tacit statistics")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (overrides --dry-run)",
    )
    parser.add_argument("--test", action="store_true", help="Run self-test suite")

    return parser.parse_args()


def cmd_test() -> int:
    """Run self-test suite."""
    print("Borg S6 Tacit — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Capture judgment
    print("\n[1/6] Capture judgment...")
    tacit = S6Tacit()
    result = tacit.capture_judgment(
        situation="Client requested rush delivery but system is at capacity",
        decision="Accept with 20% rush fee and extended timeline",
        reasoning="System capacity is the binding constraint; rush fee compensates for overtime",
        context_factors=["client is long-term partner", "system at 95% capacity"],
        outcome="accepted",
        confidence=0.85,
        tags=["operations", "client-relations"],
    )
    assert result["ok"], f"Capture failed: {result['errors']}"
    assert result["judgment"]["confidence"] == 0.85
    assert result["judgment"]["outcome"] == "accepted"
    print(f"  ✅ Judgment captured: {result['judgment']['id']}")
    passed += 1

    # Test 2: Analyze nuance
    print("\n[2/6] Analyze nuance...")
    result = tacit.analyze_nuance(
        situation="Client requested rush delivery but system is at capacity",
        similar_decisions=["previous rush request declined"],
        context="client pays premium rates",
    )
    assert result["ok"], f"Analyze failed: {result['errors']}"
    assert result["nuance_analysis"]["nuance_complexity"] in ("simple", "moderate", "complex")
    print(f"  ✅ Nuance analyzed: complexity={result['nuance_analysis']['nuance_complexity']}")
    passed += 1

    # Test 3: Route judgment
    print("\n[3/6] Route judgment...")
    result = tacit.route_judgment(
        situation="Client requested rush delivery but system is at capacity",
        decision_type="operational",
        impact_level="medium",
        reversibility="partially",
        time_pressure="urgent",
        available_expertise=["ops_manager", "account_manager"],
    )
    assert result["ok"], f"Route failed: {result['errors']}"
    assert result["routing"]["complexity_assessment"] in ("low", "medium", "high", "critical")
    print(f"  ✅ Routed: owner={result['routing']['decision_owner']}, process={result['routing']['deliberation_process']}")
    passed += 1

    # Test 4: Preserve context
    print("\n[4/6] Preserve context...")
    # Capture a judgment first to get a valid ID
    cap_result = tacit.capture_judgment(
        situation="Test situation for preservation",
        decision="Test decision",
        reasoning="Test reasoning",
    )
    judgment_id = cap_result["judgment"]["id"]
    result = tacit.preserve_context(
        judgment_id=judgment_id,
        situation_key="test situation preservation",
        applicability_scope="moderate",
        review_triggers=["system changes"],
        related_judgments=[],
    )
    assert result["ok"], f"Preserve failed: {result['errors']}"
    assert result["context_preservation"]["situation_key"] == "test situation preservation"
    print(f"  ✅ Context preserved: key='{result['context_preservation']['situation_key']}'")
    passed += 1

    # Test 5: Stats
    print("\n[5/6] Stats...")
    stats = tacit.stats()
    assert stats["total_judgments"] >= 1
    assert stats["judgments_with_outcome"] >= 1
    print(f"  ✅ Stats: {stats['total_judgments']} judgments, {stats['judgments_with_outcome']} with outcome")
    passed += 1

    # Test 6: Invalid confidence
    print("\n[6/6] Invalid confidence...")
    result = tacit.capture_judgment(
        situation="Test situation",
        decision="Test decision",
        reasoning="Test reasoning",
        confidence=1.5,  # invalid
    )
    assert not result["ok"], "Invalid confidence should fail"
    assert result["errors"], "Should have errors"
    print(f"  ✅ Invalid confidence correctly rejected: {result['errors'][0]}")
    passed += 1

    total = passed + failed
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


def main() -> int:
    args = parse_args()

    if args.test:
        return cmd_test()

    tacit = S6Tacit(vault_path=args.vault)
    tacit.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.command == "capture":
        context_factors = [
            f.strip() for f in args.context_factors.split(",") if f.strip()
        ]
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        result = tacit.capture_judgment(
            situation=args.situation,
            decision=args.decision,
            reasoning=args.reasoning,
            context_factors=context_factors,
            outcome=args.outcome or None,
            confidence=args.confidence,
            tags=tags,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = tacit.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "analyze":
        similar = [
            f.strip() for f in args.similar_decisions.split(",") if f.strip()
        ]
        result = tacit.analyze_nuance(
            situation=args.situation,
            similar_decisions=similar,
            context=args.context or None,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "route":
        expertise = [
            f.strip() for f in args.available_expertise.split(",") if f.strip()
        ]
        result = tacit.route_judgment(
            situation=args.situation,
            decision_type=args.decision_type,
            impact_level=args.impact_level,
            reversibility=args.reversibility,
            time_pressure=args.time_pressure,
            available_expertise=expertise,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "preserve":
        review_triggers = [
            f.strip() for f in args.review_triggers.split(",") if f.strip()
        ]
        related = [
            f.strip() for f in args.related_judgments.split(",") if f.strip()
        ]
        result = tacit.preserve_context(
            judgment_id=args.judgment_id,
            situation_key=args.situation_key,
            applicability_scope=args.applicability_scope,
            review_triggers=review_triggers,
            related_judgments=related,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = tacit.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "stats":
        stats = tacit.stats()
        print(json.dumps(stats, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
