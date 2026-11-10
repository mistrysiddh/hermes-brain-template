"""Borg — Phase 2: S2 Profiler Agent.

Per mem-draft-spec.txt §4 (Pipeline S2):
S2 Profiler — One rubric per record.

Each record passing S1 Ingestor gets profiled against a rubric that determines:
- Salience score (hot/cold/warm placement)
- Trust tier (verified/questionable/unverified)
- Framework eligibility
- Review queue priority
- Proactive eligibility
- Memory tier assignment (working/session/LT-hot/warm/cold)

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib
import json


# ── Rubric types ─────────────────────────────────────────────────────────

class RubricType(str, Enum):
    SALIENCE = "salience"
    TRUST = "trust"
    FRAMEWORK = "framework"
    REVIEW = "review"
    MEMORY_TIER = "memory_tier"
    PROACTIVE = "proactive"


# ── Profiler config ──────────────────────────────────────────────────────

@dataclass
class RubricConfig:
    """Configuration for a single rubric."""
    rubric_type: RubricType
    name: str
    weight: float = 1.0
    thresholds: dict[str, float] = field(default_factory=dict)
    enabled: bool = True


DEFAULT_RUBRICS: list[RubricConfig] = [
    RubricConfig(
        rubric_type=RubricType.SALIENCE,
        name="Content Salience",
        weight=0.3,
        thresholds={"high": 0.8, "medium": 0.5, "low": 0.2},
    ),
    RubricConfig(
        rubric_type=RubricType.TRUST,
        name="Trust Tier",
        weight=0.25,
        thresholds={"verified": 0.9, "questionable": 0.5, "unverified": 0.0},
    ),
    RubricConfig(
        rubric_type=RubricType.FRAMEWORK,
        name="Framework Eligibility",
        weight=0.2,
        thresholds={"eligible": 0.7, "conditional": 0.4, "not_eligible": 0.0},
    ),
    RubricConfig(
        rubric_type=RubricType.REVIEW,
        name="Review Priority",
        weight=0.15,
        thresholds={"high": 0.8, "medium": 0.5, "low": 0.2},
    ),
    RubricConfig(
        rubric_type=RubricType.PROACTIVE,
        name="Proactive Eligibility",
        weight=0.1,
        thresholds={"eligible": 0.7, "conditional": 0.4, "not_eligible": 0.0},
    ),
]


# ── Profile result ───────────────────────────────────────────────────────

@dataclass
class ProfileResult:
    """S2 Profiler result for a single record."""
    record_id: str
    record_type: str
    salience_score: float = 0.0
    trust_tier: str = "unverified"
    framework_eligible: bool = False
    review_priority: str = "low"
    proactive_eligible: bool = False
    memory_tier: str = "cold"
    rubric_scores: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    profiled_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "salience_score": self.salience_score,
            "trust_tier": self.trust_tier,
            "framework_eligible": self.framework_eligible,
            "review_priority": self.review_priority,
            "proactive_eligible": self.proactive_eligible,
            "memory_tier": self.memory_tier,
            "rubric_scores": self.rubric_scores,
            "recommendations": self.recommendations,
            "profiled_at": self.profiled_at,
        }


# ── Memory tier mapping ─────────────────────────────────────────────────

MEMORY_TIER_MAP: dict[str, str] = {
    "working": "working",
    "session": "session",
    "hot": "hot",
    "warm": "warm",
    "cold": "cold",
    "archive": "cold",
}


def score_to_tier(score: float) -> str:
    """Map salience score to memory tier."""
    if score >= 0.8:
        return "hot"
    elif score >= 0.5:
        return "warm"
    else:
        return "cold"


# ── S2 Profiler ─────────────────────────────────────────────────────────

class S2Profiler:
    """S2 Profiler agent — one rubric per record.

    Profiles records from S1 Ingestor, assigning salience, trust tier,
    framework eligibility, review priority, and memory tier.
    """

    def __init__(
        self,
        rubrics: list[RubricConfig] | None = None,
        decision_backend: Any | None = None,
    ):
        self.rubrics = rubrics or DEFAULT_RUBRICS
        self.decision_backend = decision_backend
        self._profiles: dict[str, ProfileResult] = {}

    def profile_record(
        self,
        record_id: str,
        record_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        trust_signals: dict[str, Any] | None = None,
        framework_signals: dict[str, Any] | None = None,
    ) -> ProfileResult:
        """Profile a single record against all rubrics."""
        metadata = metadata or {}
        trust_signals = trust_signals or {}
        framework_signals = framework_signals or {}

        rubric_scores: dict[str, float] = {}

        # Run each rubric
        for rubric in self.rubrics:
            if not rubric.enabled:
                continue
            score = self._score_rubric(rubric, content, metadata, trust_signals, framework_signals)
            rubric_scores[rubric.rubric_type.value] = score

        # Compute aggregate scores
        salience = rubric_scores.get(RubricType.SALIENCE.value, 0.0)
        trust_score = rubric_scores.get(RubricType.TRUST.value, 0.0)
        framework_score = rubric_scores.get(RubricType.FRAMEWORK.value, 0.0)
        review_score = rubric_scores.get(RubricType.REVIEW.value, 0.0)
        proactive_score = rubric_scores.get(RubricType.PROACTIVE.value, 0.0)

        # Determine trust tier
        if trust_score >= 0.9:
            trust_tier = "verified"
        elif trust_score >= 0.5:
            trust_tier = "questionable"
        else:
            trust_tier = "unverified"

        # Determine framework eligibility
        framework_eligible = framework_score >= 0.7

        # Determine review priority
        if review_score >= 0.8:
            review_priority = "high"
        elif review_score >= 0.5:
            review_priority = "medium"
        else:
            review_priority = "low"

        # Determine proactive eligibility
        proactive_eligible = proactive_score >= 0.7

        # Determine memory tier
        memory_tier = score_to_tier(salience)

        # Build recommendations
        recommendations: list[str] = []
        if salience >= 0.8:
            recommendations.append("promote_to_hot")
        if trust_tier == "unverified":
            recommendations.append("require_human_verification")
        if framework_eligible:
            recommendations.append("eligible_for_framework_induction")
        if review_priority == "high":
            recommendations.append("queue_for_review")
        if proactive_eligible:
            recommendations.append("enable_proactive_recall")

        profile = ProfileResult(
            record_id=record_id,
            record_type=record_type,
            salience_score=salience,
            trust_tier=trust_tier,
            framework_eligible=framework_eligible,
            review_priority=review_priority,
            proactive_eligible=proactive_eligible,
            memory_tier=memory_tier,
            rubric_scores=rubric_scores,
            recommendations=recommendations,
        )

        self._profiles[record_id] = profile
        return profile

    def _score_rubric(
        self,
        rubric: RubricConfig,
        content: str,
        metadata: dict[str, Any],
        trust_signals: dict[str, Any],
        framework_signals: dict[str, Any],
    ) -> float:
        """Score a single rubric against content and signals."""
        if self.decision_backend is not None:
            try:
                # Use Sys1 Choice primitive for scoring
                bundles = self.decision_backend.evaluate(
                    {"content": content, "metadata": json.dumps(metadata)},
                    {rubric.name: "Choice"},
                    deadline_ms=1000,
                )
                for bundle in bundles.values():
                    if bundle.selected:
                        return float(bundle.confidence)
            except Exception:
                pass

        # Deterministic fallback scoring
        return self._deterministic_score(rubric, content, metadata, trust_signals, framework_signals)

    def _deterministic_score(
        self,
        rubric: RubricConfig,
        content: str,
        metadata: dict[str, Any],
        trust_signals: dict[str, Any],
        framework_signals: dict[str, Any],
    ) -> float:
        """Deterministic fallback scoring for a rubric."""
        content_len = len(content)
        content_lower = content.lower()

        if rubric.rubric_type == RubricType.SALIENCE:
            score = 0.0
            if content_len > 1000:
                score += 0.4
            elif content_len > 200:
                score += 0.2
            if any(kw in content_lower for kw in ["important", "critical", "key", "decision"]):
                score += 0.3
            if metadata.get("source_type") in ("code", "vault"):
                score += 0.2
            if metadata.get("status") == "active":
                score += 0.1
            return min(score, 1.0)

        elif rubric.rubric_type == RubricType.TRUST:
            score = 0.5  # Neutral baseline
            if trust_signals.get("verified"):
                score += 0.4
            if trust_signals.get("trusted_source"):
                score += 0.3
            if trust_signals.get("suspicious"):
                score -= 0.4
            return max(0.0, min(score, 1.0))

        elif rubric.rubric_type == RubricType.FRAMEWORK:
            score = 0.0
            if any(kw in content_lower for kw in ["framework", "model", "approach", "methodology"]):
                score += 0.4
            if framework_signals.get("eligible"):
                score += 0.4
            if metadata.get("source_type") == "code":
                score += 0.2
            return min(score, 1.0)

        elif rubric.rubric_type == RubricType.REVIEW:
            score = 0.0
            if any(kw in content_lower for kw in ["review", "audit", "check", "verify"]):
                score += 0.4
            if metadata.get("status") == "pending":
                score += 0.3
            if trust_signals.get("questionable"):
                score += 0.3
            return min(score, 1.0)

        elif rubric.rubric_type == RubricType.PROACTIVE:
            score = 0.0
            if any(kw in content_lower for kw in ["reminder", "deadline", "upcoming", "schedule"]):
                score += 0.4
            if metadata.get("priority") == "high":
                score += 0.3
            if metadata.get("recurring"):
                score += 0.3
            return min(score, 1.0)

        return 0.0

    def profile_batch(
        self,
        records: list[dict[str, Any]],
    ) -> list[ProfileResult]:
        """Profile multiple records in batch."""
        results: list[ProfileResult] = []
        for rec in records:
            profile = self.profile_record(
                record_id=rec.get("record_id", str(len(results))),
                record_type=rec.get("record_type", "observation"),
                content=rec.get("content", ""),
                metadata=rec.get("metadata"),
                trust_signals=rec.get("trust_signals"),
                framework_signals=rec.get("framework_signals"),
            )
            results.append(profile)
        return results

    def get_profile(self, record_id: str) -> ProfileResult | None:
        """Get a previously computed profile."""
        return self._profiles.get(record_id)

    def list_profiles(self) -> list[ProfileResult]:
        """List all profiles."""
        return list(self._profiles.values())

    def stats(self) -> dict[str, Any]:
        """Profiler statistics."""
        if not self._profiles:
            return {"total": 0}
        tiers: dict[str, int] = {}
        priorities: dict[str, int] = {}
        for p in self._profiles.values():
            tiers[p.memory_tier] = tiers.get(p.memory_tier, 0) + 1
            priorities[p.review_priority] = priorities.get(p.review_priority, 0) + 1
        return {
            "total": len(self._profiles),
            "memory_tiers": tiers,
            "review_priorities": priorities,
            "framework_eligible": sum(1 for p in self._profiles.values() if p.framework_eligible),
            "proactive_eligible": sum(1 for p in self._profiles.values() if p.proactive_eligible),
        }


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S2 Profiler — one rubric per record",
    )
    parser.add_argument("--vault", required=True, help="Path to vault/store file")
    parser.add_argument("--record-id", help="Record ID to profile")
    parser.add_argument("--record-type", default="observation", help="Record type")
    parser.add_argument("--content", help="Content to profile")
    parser.add_argument("--metadata", help="JSON metadata string")
    parser.add_argument("--trust-signals", help="JSON trust signals string")
    parser.add_argument("--framework-signals", help="JSON framework signals string")
    parser.add_argument("--batch-file", help="JSON file with batch of records to profile")
    parser.add_argument("--list-profiles", action="store_true", help="List all profiles")
    parser.add_argument("--stats", action="store_true", help="Show profiler statistics")
    parser.add_argument("--test", action="store_true", help="Run self-test suite")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    parser.add_argument("--apply", action="store_true", help="Apply changes (overrides dry-run)")
    return parser.parse_args()


def cmd_test() -> int:
    """Run self-test suite."""
    print("Borg S2 Profiler — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Default rubrics
    print("\n[1/5] Default rubrics...")
    profiler = S2Profiler()
    assert len(profiler.rubrics) == 5
    print("  ✅ 5 default rubrics loaded")
    passed += 1

    # Test 2: Profile single record
    print("\n[2/5] Profile single record...")
    profile = profiler.profile_record(
        record_id="rec_001",
        record_type="observation",
        content="This is a critical decision about the system architecture framework.",
        metadata={"source_type": "code", "status": "active"},
        trust_signals={"verified": True, "trusted_source": True},
        framework_signals={"eligible": True},
    )
    assert profile.record_id == "rec_001"
    assert 0.0 <= profile.salience_score <= 1.0
    assert profile.trust_tier in ("verified", "questionable", "unverified")
    assert profile.memory_tier in ("hot", "warm", "cold")
    print(f"  ✅ Profile created: salience={profile.salience_score:.2f}, trust={profile.trust_tier}, tier={profile.memory_tier}")
    passed += 1

    # Test 3: Profile batch
    print("\n[3/5] Profile batch...")
    batch = [
        {"record_id": "r1", "record_type": "observation", "content": "High priority task deadline approaching."},
        {"record_id": "r2", "record_type": "entity", "content": "Reference material for background."},
    ]
    results = profiler.profile_batch(batch)
    assert len(results) == 2
    assert results[0].record_id == "r1"
    assert results[1].record_id == "r2"
    print(f"  ✅ Batch profile: {len(results)} records profiled")
    passed += 1

    # Test 4: Get profile
    print("\n[4/5] Get profile...")
    retrieved = profiler.get_profile("rec_001")
    assert retrieved is not None
    assert retrieved.record_id == "rec_001"
    print("  ✅ Profile retrieval works")
    passed += 1

    # Test 5: Stats
    print("\n[5/5] Stats...")
    stats = profiler.stats()
    assert stats["total"] == 3  # 1 single + 2 batch
    print(f"  ✅ Stats: {stats['total']} total profiles")
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

    profiler = S2Profiler()

    if args.list_profiles:
        profiles = profiler.list_profiles()
        print(f"Profiles ({len(profiles)}):")
        for p in profiles:
            print(f"  {p.record_id}: salience={p.salience_score:.2f}, trust={p.trust_tier}, tier={p.memory_tier}, priority={p.review_priority}")
        return 0

    if args.stats:
        stats = profiler.stats()
        print("Profiler Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return 0

    if args.batch_file:
        import json
        with open(args.batch_file) as f:
            batch = json.load(f)
        results = profiler.profile_batch(batch)
        for p in results:
            print(f"{p.record_id}: salience={p.salience_score:.2f}, trust={p.trust_tier}, tier={p.memory_tier}")
        return 0

    if args.record_id and args.content:
        metadata = json.loads(args.metadata) if args.metadata else {}
        trust_signals = json.loads(args.trust_signals) if args.trust_signals else {}
        framework_signals = json.loads(args.framework_signals) if args.framework_signals else {}

        profile = profiler.profile_record(
            record_id=args.record_id,
            record_type=args.record_type,
            content=args.content,
            metadata=metadata,
            trust_signals=trust_signals,
            framework_signals=framework_signals,
        )
        print(f"Profile for {profile.record_id}:")
        print(f"  Salience: {profile.salience_score:.2f}")
        print(f"  Trust: {profile.trust_tier}")
        print(f"  Framework eligible: {profile.framework_eligible}")
        print(f"  Review priority: {profile.review_priority}")
        print(f"  Proactive eligible: {profile.proactive_eligible}")
        print(f"  Memory tier: {profile.memory_tier}")
        print(f"  Recommendations: {', '.join(profile.recommendations) or 'none'}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
