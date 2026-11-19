"""Borg — Phase 2: S7 Dedup Agent.

Per mem-draft-spec.txt §4 (Pipeline S7):
S7 Dedup — Canonicalize + diversity.

Detects duplicate records, canonicalizes them into single records,
resolves merge conflicts, and promotes diversity across sources/types.

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


S7_CANONICALIZE_PROMPT = _load_prompt_file("s7_canonicalize_prompt")
S7_DIVERSITY_PROMPT = _load_prompt_file("s7_diversity_prompt")
S7_SIMILARITY_PROMPT = _load_prompt_file("s7_similarity_prompt")
S7_MERGE_RESOLVE_PROMPT = _load_prompt_file("s7_merge_resolve_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Types ────────────────────────────────────────────────────────────────

@dataclass
class CanonicalRecord:
    """A canonical record after dedup."""

    canonical_id: str
    source_record_ids: list[str] = field(default_factory=list)
    merged_fields: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    record: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "source_record_ids": list(self.source_record_ids),
            "merged_fields": list(self.merged_fields),
            "conflicts": list(self.conflicts),
            "record": self.record,
        }


@dataclass
class SimilarityResult:
    """Result of computing similarity between two records."""

    similarity: float
    field_similarities: dict[str, float] = field(default_factory=dict)
    matching_fields: list[str] = field(default_factory=list)
    differing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "similarity": self.similarity,
            "field_similarities": dict(self.field_similarities),
            "matching_fields": list(self.matching_fields),
            "differing_fields": list(self.differing_fields),
        }


@dataclass
class MergeResolution:
    """Result of resolving a merge conflict."""

    field_name: str
    resolved_value: Any
    resolution_method: str
    rationale: str
    alternative_values: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "resolved_value": self.resolved_value,
            "resolution_method": self.resolution_method,
            "rationale": self.rationale,
            "alternative_values": list(self.alternative_values),
        }


@dataclass
class DiversityMetrics:
    """Diversity metrics before/after filtering."""

    before: float
    after: float
    improvement: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "before": self.before,
            "after": self.after,
            "improvement": self.improvement,
        }


# ── Helper functions ─────────────────────────────────────────────────────

def _record_id(record: dict[str, Any]) -> str:
    """Generate a deterministic record ID."""
    content = json.dumps(record, sort_keys=True)
    h = hashlib.sha256(content.encode()).hexdigest()[:12]
    return f"r:{h}"


def _char_3grams(text: str) -> set[str]:
    """Generate character 3-grams for similarity comparison."""
    text = text.lower()
    return {text[i:i+3] for i in range(len(text) - 2)}


def _jaccard_similarity(a: str, b: str) -> float:
    """Jaccard similarity on character 3-grams."""
    grams_a = _char_3grams(a)
    grams_b = _char_3grams(b)
    if not grams_a and not grams_b:
        return 1.0
    if not grams_a or not grams_b:
        return 0.0
    intersection = len(grams_a & grams_b)
    union = len(grams_a | grams_b)
    return intersection / union if union > 0 else 0.0


def _field_similarity(val_a: Any, val_b: Any) -> float:
    """Compute similarity between two field values."""
    if val_a == val_b:
        return 1.0
    if isinstance(val_a, str) and isinstance(val_b, str):
        return _jaccard_similarity(val_a, val_b)
    if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
        if val_a == 0 and val_b == 0:
            return 1.0
        max_val = max(abs(val_a), abs(val_b))
        if max_val == 0:
            return 1.0
        return 1.0 - abs(val_a - val_b) / max_val
    return 0.0


# ── Step 1: Similarity ───────────────────────────────────────────────────

def step_similarity(
    record_a: dict[str, Any],
    record_b: dict[str, Any],
    fields: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> tuple[SimilarityResult, list[str]]:
    """Compute similarity between two records.

    Returns (similarity_result, errors).
    """
    errors: list[str] = []
    fields = fields or list(set(list(record_a.keys()) + list(record_b.keys())))
    weights = weights or {}

    field_sims: dict[str, float] = {}
    matching: list[str] = []
    differing: list[str] = []

    total_weight = 0.0
    weighted_sum = 0.0

    for field in fields:
        val_a = record_a.get(field)
        val_b = record_b.get(field)
        sim = _field_similarity(val_a, val_b)
        weight = weights.get(field, 1.0)
        field_sims[field] = sim
        total_weight += weight
        weighted_sum += sim * weight

        if sim == 1.0:
            matching.append(field)
        else:
            differing.append(field)

    overall = weighted_sum / total_weight if total_weight > 0 else 0.0

    return SimilarityResult(
        similarity=round(overall, 4),
        field_similarities=field_sims,
        matching_fields=matching,
        differing_fields=differing,
    ), errors


# ── Step 2: Canonicalize ─────────────────────────────────────────────────

def step_canonicalize(
    records: list[dict[str, Any]],
    similarity_threshold: float = 0.85,
    merge_strategy: str = "union",
) -> tuple[list[CanonicalRecord], list[dict[str, Any]], list[str]]:
    """Canonicalize duplicate records.

    Returns (canonical_records, unmerged_records, errors).
    """
    errors: list[str] = []
    if not records:
        return [], [], errors

    # Assign IDs to records
    for rec in records:
        if "id" not in rec:
            rec["id"] = _record_id(rec)

    # Find duplicate clusters using union-find
    parent: dict[str, str] = {rec["id"]: rec["id"] for rec in records}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # Compare all pairs
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            sim_result, _ = step_similarity(
                records[i], records[j],
                fields=None,
                weights=None,
            )
            if sim_result.similarity >= similarity_threshold:
                union(records[i]["id"], records[j]["id"])

    # Group by cluster root
    clusters: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        root = find(rec["id"])
        clusters.setdefault(root, []).append(rec)

    canonical_records: list[CanonicalRecord] = []
    unmerged_records: list[dict[str, Any]] = []
    total_duplicates_removed = 0

    for root, cluster in clusters.items():
        if len(cluster) == 1:
            unmerged_records.append(cluster[0])
            continue

        # Select canonical record (highest confidence or most complete)
        def completeness(rec: dict[str, Any]) -> float:
            non_empty = sum(1 for v in rec.values() if v is not None and v != "")
            return non_empty / max(len(rec), 1)

        def confidence(rec: dict[str, Any]) -> float:
            return float(rec.get("confidence", 0.5))

        canonical = max(cluster, key=lambda r: (confidence(r), completeness(r)))
        canonical_id = _record_id(canonical["record"] if isinstance(canonical.get("record"), dict) else canonical)

        # Merge fields
        merged_fields: list[str] = []
        conflicts: list[str] = []
        merged_record: dict[str, Any] = dict(canonical)

        all_fields = set()
        for rec in cluster:
            all_fields.update(rec.keys())

        for field in all_fields:
            values = [rec.get(field) for rec in cluster if field in rec]
            if not values:
                continue
            unique_values = list(dict.fromkeys(values))  # preserve order, dedup
            if len(unique_values) == 1:
                merged_record[field] = unique_values[0]
                merged_fields.append(field)
            else:
                conflicts.append(field)
                # Resolution: prefer highest confidence
                best_idx = max(range(len(values)), key=lambda i: float(cluster[i].get("confidence", 0.5)))
                merged_record[field] = values[best_idx]
                merged_fields.append(field)

        canonical_records.append(CanonicalRecord(
            canonical_id=canonical_id,
            source_record_ids=[rec["id"] for rec in cluster],
            merged_fields=merged_fields,
            conflicts=conflicts,
            record=merged_record,
        ))
        total_duplicates_removed += len(cluster) - 1

    return canonical_records, unmerged_records, errors


# ── Step 3: Merge Resolve ────────────────────────────────────────────────

def step_merge_resolve(
    field_name: str,
    values: list[Any],
    confidences: list[float] | None = None,
    sources: list[str] | None = None,
) -> tuple[MergeResolution, list[str]]:
    """Resolve a merge conflict.

    Returns (resolution, errors).
    """
    errors: list[str] = []
    confidences = confidences or [0.5] * len(values)
    sources = sources or [f"source_{i}" for i in range(len(values))]

    if not values:
        errors.append("No values to resolve")
        return MergeResolution(
            field_name=field_name,
            resolved_value=None,
            resolution_method="error",
            rationale="No values provided",
        ), errors

    unique_values = list(dict.fromkeys(values))
    if len(unique_values) == 1:
        return MergeResolution(
            field_name=field_name,
            resolved_value=unique_values[0],
            resolution_method="identical",
            rationale="All values are identical",
        ), errors

    # Find highest confidence
    best_idx = max(range(len(values)), key=lambda i: confidences[i])
    best_value = values[best_idx]
    best_confidence = confidences[best_idx]

    # Check if second-best is close
    sorted_indices = sorted(range(len(values)), key=lambda i: confidences[i], reverse=True)
    if len(sorted_indices) > 1:
        second_confidence = confidences[sorted_indices[1]]
        if best_confidence - second_confidence < 0.1:
            method = "ambiguous"
            rationale = f"Confidences too close ({best_confidence:.2f} vs {second_confidence:.2f}), using highest confidence"
        else:
            method = "highest_confidence"
            rationale = f"Highest confidence ({best_confidence:.2f}) selected"
    else:
        method = "highest_confidence"
        rationale = f"Only one value with confidence {best_confidence:.2f}"

    return MergeResolution(
        field_name=field_name,
        resolved_value=best_value,
        resolution_method=method,
        rationale=rationale,
        alternative_values=[v for i, v in enumerate(values) if i != best_idx],
    ), errors


# ── Step 4: Diversity ────────────────────────────────────────────────────

def step_diversity(
    records: list[dict[str, Any]],
    diversity_dimensions: list[str],
    max_per_dimension: int = 3,
    min_representation: int = 1,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], DiversityMetrics, list[str]]:
    """Promote diversity across records.

    Returns (diversified_records, removed_records, metrics, errors).
    """
    errors: list[str] = []
    if not records:
        return [], [], DiversityMetrics(before=0.0, after=0.0, improvement=0.0), errors

    # Compute diversity before
    def compute_diversity(recs: list[dict[str, Any]]) -> float:
        if not recs:
            return 0.0
        total_entropy = 0.0
        for dim in diversity_dimensions:
            values: dict[str, int] = {}
            for rec in recs:
                v = rec.get(dim, "unknown")
                values[v] = values.get(v, 0) + 1
            total = len(recs)
            entropy = 0.0
            for count in values.values():
                p = count / total
                if p > 0:
                    entropy -= p * __import__("math").log(p)
            max_entropy = __import__("math").log(len(values)) if len(values) > 1 else 1.0
            if max_entropy > 0:
                total_entropy += entropy / max_entropy
        return total_entropy / len(diversity_dimensions) if diversity_dimensions else 0.0

    before = compute_diversity(records)

    # Group by dimension values
    dimension_groups: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for dim in diversity_dimensions:
        dimension_groups[dim] = {}
        for rec in records:
            v = rec.get(dim, "unknown")
            dimension_groups[dim].setdefault(v, []).append(rec)

    # Select records to keep
    keep_ids: set[str] = set()
    removed_records: list[dict[str, Any]] = []

    for dim in diversity_dimensions:
        for value, recs in dimension_groups[dim].items():
            if len(recs) <= max_per_dimension:
                # Keep all (under or at limit)
                for rec in recs:
                    keep_ids.add(rec.get("id", _record_id(rec)))
            else:
                # Over-represented: keep max_per_dimension, prefer highest confidence
                sorted_recs = sorted(
                    recs,
                    key=lambda r: float(r.get("confidence", 0.5)),
                    reverse=True,
                )
                # Ensure min_representation
                keep_count = max(max_per_dimension, min_representation)
                for rec in sorted_recs[:keep_count]:
                    keep_ids.add(rec.get("id", _record_id(rec)))
                for rec in sorted_recs[keep_count:]:
                    removed_records.append(rec)

    # Build diversified list
    diversified_records = [
        rec for rec in records
        if rec.get("id", _record_id(rec)) in keep_ids
    ]

    after = compute_diversity(diversified_records)

    # Dimension distribution after
    dimension_distribution: dict[str, dict[str, int]] = {}
    for dim in diversity_dimensions:
        dimension_distribution[dim] = {}
        for rec in diversified_records:
            v = rec.get(dim, "unknown")
            dimension_distribution[dim][v] = dimension_distribution[dim].get(v, 0) + 1

    metrics = DiversityMetrics(
        before=round(before, 4),
        after=round(after, 4),
        improvement=round(after - before, 4),
    )

    return diversified_records, removed_records, metrics, errors


# ── S7 Dedup Agent ───────────────────────────────────────────────────────

class S7Dedup:
    """S7 Dedup agent — Canonicalize + diversity.

    Detects duplicates, canonicalizes them, resolves merge conflicts,
    and promotes diversity across records.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._canonical_records: list[CanonicalRecord] = []
        self._unmerged_records: list[dict[str, Any]] = []
        self._diversified_records: list[dict[str, Any]] = []
        self._diversity_metrics: DiversityMetrics | None = None

    # ── Similarity ──────────────────────────────────────────────────

    def compute_similarity(
        self,
        record_a: dict[str, Any],
        record_b: dict[str, Any],
        fields: list[str] | None = None,
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Compute similarity between two records."""
        result, errors = step_similarity(record_a, record_b, fields, weights)
        return {
            "similarity": result.similarity,
            "field_similarities": result.field_similarities,
            "matching_fields": result.matching_fields,
            "differing_fields": result.differing_fields,
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Canonicalize ────────────────────────────────────────────────

    def canonicalize(
        self,
        records: list[dict[str, Any]],
        similarity_threshold: float = 0.85,
        merge_strategy: str = "union",
    ) -> dict[str, Any]:
        """Canonicalize duplicate records."""
        canonical, unmerged, errors = step_canonicalize(
            records, similarity_threshold, merge_strategy
        )
        self._canonical_records = canonical
        self._unmerged_records = unmerged
        return {
            "canonical_records": [c.to_dict() for c in canonical],
            "unmerged_records": unmerged,
            "total_clusters": len(canonical) + len(unmerged),
            "total_duplicates_removed": sum(
                len(c.source_record_ids) - 1 for c in canonical
            ),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Merge Resolve ───────────────────────────────────────────────

    def merge_resolve(
        self,
        field_name: str,
        values: list[Any],
        confidences: list[float] | None = None,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Resolve a merge conflict."""
        resolution, errors = step_merge_resolve(field_name, values, confidences, sources)
        return {
            "field_name": resolution.field_name,
            "resolved_value": resolution.resolved_value,
            "resolution_method": resolution.resolution_method,
            "rationale": resolution.rationale,
            "alternative_values": resolution.alternative_values,
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Diversity ───────────────────────────────────────────────────

    def promote_diversity(
        self,
        records: list[dict[str, Any]],
        diversity_dimensions: list[str],
        max_per_dimension: int = 3,
        min_representation: int = 1,
    ) -> dict[str, Any]:
        """Promote diversity across records."""
        diversified, removed, metrics, errors = step_diversity(
            records, diversity_dimensions, max_per_dimension, min_representation
        )
        self._diversified_records = diversified
        self._diversity_metrics = metrics
        return {
            "diversified_records": diversified,
            "removed_records": removed,
            "diversity_metrics": metrics.to_dict(),
            "dimension_distribution": {
                dim: {
                    v: sum(1 for r in diversified if r.get(dim) == v)
                    for v in set(r.get(dim, "unknown") for r in diversified)
                }
                for dim in diversity_dimensions
            },
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Dedup statistics."""
        return {
            "total_canonical_records": len(self._canonical_records),
            "total_unmerged_records": len(self._unmerged_records),
            "total_diversified_records": len(self._diversified_records),
            "diversity_metrics": self._diversity_metrics.to_dict() if self._diversity_metrics else None,
        }

    # ── Persistence ────────────────────────────────────────────────

    def save_to_vault(self, apply: bool = False) -> str | None:
        """Save dedup data to vault as JSON (if --apply / vault configured)."""
        if not self.vault_path or not apply:
            return None

        dir_path = self.vault_path / "02-Areas" / "Skills"
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {
            "canonical_records": [c.to_dict() for c in self._canonical_records],
            "unmerged_records": self._unmerged_records,
            "diversified_records": self._diversified_records,
            "diversity_metrics": self._diversity_metrics.to_dict() if self._diversity_metrics else None,
            "stats": self.stats(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        path = dir_path / "dedup-results.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def load_from_vault(self) -> bool:
        """Load dedup data from vault JSON file."""
        if not self.vault_path:
            return False

        path = self.vault_path / "02-Areas" / "Skills" / "dedup-results.json"
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for cr in data.get("canonical_records", []):
                self._canonical_records.append(CanonicalRecord(**cr))
            self._unmerged_records = data.get("unmerged_records", [])
            self._diversified_records = data.get("diversified_records", [])
            if data.get("diversity_metrics"):
                dm = data["diversity_metrics"]
                self._diversity_metrics = DiversityMetrics(
                    before=dm["before"],
                    after=dm["after"],
                    improvement=dm["improvement"],
                )
            return True
        except (json.JSONDecodeError, TypeError, KeyError):
            return False


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S7 Dedup — Canonicalize + diversity",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")

    sub = parser.add_subparsers(dest="command")

    # similarity
    p_sim = sub.add_parser("similarity", help="Compute similarity between two records")
    p_sim.add_argument("--record-a", required=True, help="JSON file or JSON string for record A")
    p_sim.add_argument("--record-b", required=True, help="JSON file or JSON string for record B")
    p_sim.add_argument("--fields", default="", help="Comma-separated fields to compare")
    p_sim.add_argument("--weights", default="", help="JSON string for field weights")

    # canonicalize
    p_canon = sub.add_parser("canonicalize", help="Canonicalize duplicate records")
    p_canon.add_argument(
        "--records-json", required=True, help="JSON file with records list"
    )
    p_canon.add_argument(
        "--similarity-threshold", type=float, default=0.85, help="Similarity threshold"
    )
    p_canon.add_argument(
        "--merge-strategy", default="union", help="Merge strategy (union/intersection/highest_confidence)"
    )

    # merge-resolve
    p_merge = sub.add_parser("merge-resolve", help="Resolve a merge conflict")
    p_merge.add_argument("--field-name", required=True, help="Field name")
    p_merge.add_argument(
        "--values", required=True, help="JSON list of values"
    )
    p_merge.add_argument(
        "--confidences", default="", help="JSON list of confidences"
    )
    p_merge.add_argument(
        "--sources", default="", help="JSON list of sources"
    )

    # diversity
    p_div = sub.add_parser("diversity", help="Promote diversity across records")
    p_div.add_argument(
        "--records-json", required=True, help="JSON file with records list"
    )
    p_div.add_argument(
        "--dimensions", required=True, help="Comma-separated diversity dimensions"
    )
    p_div.add_argument(
        "--max-per-dimension", type=int, default=3, help="Max records per dimension value"
    )
    p_div.add_argument(
        "--min-representation", type=int, default=1, help="Min records per dimension value"
    )

    # stats
    sub.add_parser("stats", help="Show dedup statistics")

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
    print("Borg S7 Dedup — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Similarity
    print("\n[1/6] Compute similarity...")
    dedup = S7Dedup()
    result = dedup.compute_similarity(
        record_a={"title": "Hello World", "author": "Alice", "score": 0.9},
        record_b={"title": "Hello World!", "author": "Alice", "score": 0.85},
    )
    assert result["ok"], f"Similarity failed: {result['errors']}"
    assert 0.0 <= result["similarity"] <= 1.0
    print(f"  ✅ Similarity: {result['similarity']}")
    passed += 1

    # Test 2: Canonicalize
    print("\n[2/6] Canonicalize records...")
    records = [
        {"id": "r1", "title": "Project Alpha", "author": "Bob", "confidence": 0.9},
        {"id": "r2", "title": "Project Alpha", "author": "Bob", "confidence": 0.7},
        {"id": "r3", "title": "Project Beta", "author": "Carol", "confidence": 0.8},
    ]
    result = dedup.canonicalize(records, similarity_threshold=0.8)
    assert result["ok"], f"Canonicalize failed: {result['errors']}"
    assert result["total_duplicates_removed"] >= 1
    print(f"  ✅ Canonicalized: {result['total_clusters']} clusters, {result['total_duplicates_removed']} duplicates removed")
    passed += 1

    # Test 3: Merge resolve
    print("\n[3/6] Merge resolve...")
    result = dedup.merge_resolve(
        field_name="priority",
        values=["high", "medium", "high"],
        confidences=[0.9, 0.5, 0.8],
        sources=["src1", "src2", "src3"],
    )
    assert result["ok"], f"Merge resolve failed: {result['errors']}"
    assert result["resolved_value"] == "high"
    print(f"  ✅ Resolved: {result['resolved_value']} ({result['resolution_method']})")
    passed += 1

    # Test 4: Diversity
    print("\n[4/6] Promote diversity...")
    records = [
        {"id": "d1", "source": "A", "type": "bug", "confidence": 0.9},
        {"id": "d2", "source": "A", "type": "feature", "confidence": 0.8},
        {"id": "d3", "source": "A", "type": "docs", "confidence": 0.7},
        {"id": "d4", "source": "B", "type": "bug", "confidence": 0.6},
    ]
    result = dedup.promote_diversity(
        records,
        diversity_dimensions=["source", "type"],
        max_per_dimension=2,
    )
    assert result["ok"], f"Diversity failed: {result['errors']}"
    assert result["diversity_metrics"]["after"] >= result["diversity_metrics"]["before"]
    print(f"  ✅ Diversity: before={result['diversity_metrics']['before']}, after={result['diversity_metrics']['after']}")
    passed += 1

    # Test 5: Stats
    print("\n[5/6] Stats...")
    stats = dedup.stats()
    assert "total_canonical_records" in stats
    assert "total_diversified_records" in stats
    print(f"  ✅ Stats: {stats['total_canonical_records']} canonical, {stats['total_diversified_records']} diversified")
    passed += 1

    # Test 6: Identical values merge
    print("\n[6/6] Identical values merge resolve...")
    result = dedup.merge_resolve(
        field_name="status",
        values=["active", "active", "active"],
        confidences=[0.5, 0.5, 0.5],
    )
    assert result["ok"]
    assert result["resolved_value"] == "active"
    assert result["resolution_method"] == "identical"
    print(f"  ✅ Identical merge: {result['resolved_value']} ({result['resolution_method']})")
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

    dedup = S7Dedup(vault_path=args.vault)
    dedup.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.command == "similarity":
        import json as _json
        try:
            record_a = _json.loads(args.record_a)
        except _json.JSONDecodeError:
            try:
                record_a = _json.loads(_json.dumps(args.record_a))
            except Exception:
                record_a = {"content": args.record_a}
        try:
            record_b = _json.loads(args.record_b)
        except _json.JSONDecodeError:
            try:
                record_b = _json.loads(_json.dumps(args.record_b))
            except Exception:
                record_b = {"content": args.record_b}
        fields = [f.strip() for f in args.fields.split(",") if f.strip()] or None
        weights = _json.loads(args.weights) if args.weights else None
        result = dedup.compute_similarity(record_a, record_b, fields, weights)
        print(_json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "canonicalize":
        import json as _json
        with open(args.records_json) as f:
            records = _json.load(f)
        result = dedup.canonicalize(
            records,
            similarity_threshold=args.similarity_threshold,
            merge_strategy=args.merge_strategy,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = dedup.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "merge-resolve":
        import json as _json
        values = _json.loads(args.values)
        confidences = _json.loads(args.confidences) if args.confidences else None
        sources = _json.loads(args.sources) if args.sources else None
        result = dedup.merge_resolve(args.field_name, values, confidences, sources)
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = dedup.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "diversity":
        import json as _json
        with open(args.records_json) as f:
            records = _json.load(f)
        dimensions = [d.strip() for d in args.dimensions.split(",") if d.strip()]
        result = dedup.promote_diversity(
            records,
            diversity_dimensions=dimensions,
            max_per_dimension=args.max_per_dimension,
            min_representation=args.min_representation,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = dedup.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "stats":
        stats = dedup.stats()
        print(_json.dumps(stats, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
