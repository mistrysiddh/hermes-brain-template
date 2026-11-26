"""Borg — Phase 2: S4 Skids Agent.

Per mem-draft-spec.txt §4 (Pipeline S4):
S4 Skids — Find L0 primitives.

Detects L0 primitives (smallest irreducible units of actionable knowledge)
from raw material, catalogs them into searchable indexes, and supports
search and deduplication across catalogs.

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
import re


# ── Sub-prompt loading ───────────────────────────────────────────────────
_cli_dir = Path(__file__).resolve().parent
_prompts_dir = _cli_dir / "prompts"


def _load_prompt_file(name: str) -> str:
    path = _prompts_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


S4_PRIMITIVE_DETECT_PROMPT = _load_prompt_file("s4_primitive_detect_prompt")
S4_PRIMITIVE_CATALOG_PROMPT = _load_prompt_file("s4_primitive_catalog_prompt")
S4_PRIMITIVE_SEARCH_PROMPT = _load_prompt_file("s4_primitive_search_prompt")
S4_PRIMITIVE_DEDUP_PROMPT = _load_prompt_file("s4_primitive_dedup_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Types ────────────────────────────────────────────────────────────────

PRIMITIVE_TYPES = {"action", "fact", "decision", "question", "reference", "warning"}


@dataclass
class Primitive:
    """An L0 primitive — smallest irreducible unit of actionable knowledge."""

    id: str
    text: str
    type: str
    confidence: float
    source_location: str
    size: int
    catalog: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type,
            "confidence": self.confidence,
            "source_location": self.source_location,
            "size": self.size,
            "catalog": self.catalog,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Primitive":
        return cls(
            id=data["id"],
            text=data["text"],
            type=data["type"],
            confidence=data["confidence"],
            source_location=data["source_location"],
            size=data["size"],
            catalog=data.get("catalog", ""),
            tags=data.get("tags", []),
        )


@dataclass
class Catalog:
    """A catalog of primitives."""

    name: str
    created_at: str
    primitives: dict[str, Primitive] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "total_primitives": len(self.primitives),
            "tags": list(self.tags),
        }


# ── Helper functions ─────────────────────────────────────────────────────

def _primitive_id(text: str, catalog: str) -> str:
    """Generate a deterministic primitive ID from text + catalog."""
    h = hashlib.sha256(f"{catalog}:{text}".encode()).hexdigest()[:12]
    return f"p:{h}"


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


def _split_into_candidates(content: str) -> list[str]:
    """Split content into candidate primitive boundaries."""
    # Split on sentence boundaries, bullet points, and blank lines
    candidates: list[str] = []
    # First split by double newlines (paragraphs)
    paragraphs = re.split(r"\n\s*\n", content)
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Split by sentence-ending punctuation followed by space/newline
        sentences = re.split(r"(?<=[.!?])\s+", para)
        for sent in sentences:
            sent = sent.strip()
            if sent:
                candidates.append(sent)
        # Also treat bullet points as separate candidates
        bullets = re.split(r"\n[-*•]\s+", para)
        for bullet in bullets:
            bullet = bullet.strip()
            if bullet and bullet != candidates[-1] if candidates else True:
                if bullet and bullet not in candidates:
                    candidates.append(bullet)
    return candidates


# ── Step 1: Primitive Detect ─────────────────────────────────────────────

def step_detect(
    content: str,
    min_size: int = 20,
    max_size: int = 500,
) -> tuple[list[Primitive], list[str]]:
    """Detect L0 primitives from raw content.

    Returns (primitives, errors).
    """
    errors: list[str] = []
    primitives: list[Primitive] = []

    if not content or not content.strip():
        return [], ["Content is empty"]

    candidates = _split_into_candidates(content)

    seen_texts: set[str] = set()
    for candidate in candidates:
        text = candidate.strip()
        if not text:
            continue
        if len(text) < min_size:
            continue
        if len(text) > max_size:
            continue
        # Deduplicate exact text
        if text in seen_texts:
            continue
        seen_texts.add(text)

        # Classify type
        ptype = _classify_primitive(text)
        confidence = _compute_confidence(text, ptype)

        primitives.append(Primitive(
            id="",  # assigned later
            text=text,
            type=ptype,
            confidence=confidence,
            source_location="",
            size=len(text),
        ))

    # Sort by confidence descending
    primitives.sort(key=lambda p: p.confidence, reverse=True)

    # Assign IDs
    for i, p in enumerate(primitives):
        p.id = f"p{i:04d}"
        p.source_location = f"candidate-{i}"

    return primitives, errors


def _classify_primitive(text: str) -> str:
    """Classify a primitive by type based on content patterns."""
    lower = text.lower()
    if any(kw in lower for kw in ["should", "must", "will", "shall", "need to", "has to"]):
        return "action"
    if any(kw in lower for kw in ["?", "what", "why", "how", "when", "where", "who"]):
        return "question"
    if any(kw in lower for kw in ["decided", "decision", "chose", "selected", "agreed"]):
        return "decision"
    if any(kw in lower for kw in ["warning", "caution", "alert", "danger", "beware", "risk"]):
        return "warning"
    if any(kw in lower for kw in ["see", "reference", "link", "url", "doc", "document"]):
        return "reference"
    return "fact"


def _compute_confidence(text: str, ptype: str) -> float:
    """Compute confidence score for a primitive."""
    score = 0.5  # base
    if len(text) >= 30:
        score += 0.2
    if len(text) >= 100:
        score += 0.1
    if ptype in ("action", "decision"):
        score += 0.1
    if text[0].isupper() and text[-1] in (".", "!", "?"):
        score += 0.1
    return min(score, 1.0)


# ── Step 2: Primitive Catalog ────────────────────────────────────────────

@dataclass
class CatalogIndex:
    """Search index for a catalog."""

    keywords: dict[str, set[str]] = field(default_factory=dict)  # keyword -> primitive ids
    by_type: dict[str, set[str]] = field(default_factory=dict)  # type -> primitive ids


def step_catalog(
    primitives: list[Primitive],
    catalog_name: str,
    tags: list[str] | None = None,
) -> tuple[Catalog, CatalogIndex, list[str]]:
    """Catalog primitives into a searchable index.

    Returns (catalog, index, errors).
    """
    errors: list[str] = []
    tags = tags or []

    created_at = datetime.now(timezone.utc).isoformat()
    catalog = Catalog(name=catalog_name, created_at=created_at, tags=list(tags))
    index = CatalogIndex()

    for p in primitives:
        p.catalog = catalog_name
        p.tags = list(tags)
        catalog.primitives[p.id] = p

        # Keyword index
        words = set(re.findall(r"\w+", p.text.lower()))
        for w in words:
            index.keywords.setdefault(w, set()).add(p.id)

        # Type index
        index.by_type.setdefault(p.type, set()).add(p.id)

    return catalog, index, errors


# ── Step 3: Primitive Search ─────────────────────────────────────────────

def step_search(
    catalog: Catalog,
    index: CatalogIndex,
    query: str,
    type_filter: str | None = None,
    min_confidence: float | None = None,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Search the primitive catalog.

    Returns (results, errors).
    """
    errors: list[str] = []
    keywords = set(re.findall(r"\w+", query.lower()))

    if not keywords:
        return [], []

    # Collect candidate primitive IDs
    candidate_ids: set[str] = set()
    for kw in keywords:
        if kw in index.keywords:
            candidate_ids.update(index.keywords[kw])

    if not candidate_ids:
        return [], []

    # Filter by type and confidence
    filtered: list[Primitive] = []
    for pid in candidate_ids:
        p = catalog.primitives.get(pid)
        if not p:
            continue
        if type_filter and p.type != type_filter:
            continue
        if min_confidence is not None and p.confidence < min_confidence:
            continue
        filtered.append(p)

    # Score results
    results: list[dict[str, Any]] = []
    for p in filtered:
        p_words = set(re.findall(r"\w+", p.text.lower()))
        matched = keywords & p_words
        score = (len(matched) / len(keywords)) * 0.5 + p.confidence * 0.5
        results.append({
            "primitive_id": p.id,
            "text": p.text,
            "type": p.type,
            "confidence": p.confidence,
            "score": round(score, 4),
            "matched_keywords": sorted(matched),
        })

    # Sort by score desc, then confidence desc
    results.sort(key=lambda r: (r["score"], r["confidence"]), reverse=True)
    results = results[:limit]

    return results, errors


# ── Step 4: Primitive Deduplicate ────────────────────────────────────────

def step_dedup(
    catalogs: dict[str, Catalog],
    indices: dict[str, CatalogIndex],
    similarity_threshold: float = 0.9,
    keep_strategy: str = "highest_confidence",
) -> tuple[dict[str, Any], list[str]]:
    """Deduplicate primitives across catalogs.

    Returns (summary, errors).
    """
    errors: list[str] = []

    if keep_strategy not in ("highest_confidence", "first_seen"):
        errors.append(f"Invalid keep_strategy: {keep_strategy}")
        return {}, errors

    # Collect all primitives
    all_primitives: list[tuple[str, str, Primitive]] = []  # (catalog_name, primitive_id, primitive)
    for cat_name, catalog in catalogs.items():
        for pid, p in catalog.primitives.items():
            all_primitives.append((cat_name, pid, p))

    total_before = len(all_primitives)
    duplicates: set[tuple[str, str]] = set()  # (catalog_name, primitive_id) to remove

    # Compare each pair
    for i in range(len(all_primitives)):
        cat_i, pid_i, p_i = all_primitives[i]
        if (cat_i, pid_i) in duplicates:
            continue
        for j in range(i + 1, len(all_primitives)):
            cat_j, pid_j, p_j = all_primitives[j]
            if (cat_j, pid_j) in duplicates:
                continue
            similarity = _jaccard_similarity(p_i.text, p_j.text)
            if similarity >= similarity_threshold:
                # Decide which to remove
                if keep_strategy == "highest_confidence":
                    if p_i.confidence >= p_j.confidence:
                        duplicates.add((cat_j, pid_j))
                    else:
                        duplicates.add((cat_i, pid_i))
                else:  # first_seen
                    duplicates.add((cat_j, pid_j))

    # Remove duplicates from catalogs and indices
    for cat_name, pid in duplicates:
        if cat_name in catalogs and pid in catalogs[cat_name].primitives:
            del catalogs[cat_name].primitives[pid]
        if cat_name in indices and pid in indices[cat_name].keywords:
            # Remove from keyword index
            for kw, ids in indices[cat_name].keywords.items():
                ids.discard(pid)
            # Remove from type index
            for t, ids in indices[cat_name].by_type.items():
                ids.discard(pid)

    total_after = total_before - len(duplicates)

    summary = {
        "scanned_catalogs": sorted(catalogs.keys()),
        "total_primitives_before": total_before,
        "duplicates_removed": len(duplicates),
        "total_primitives_after": total_after,
        "similarity_threshold": similarity_threshold,
    }

    return summary, errors


# ── S4 Skids Agent ───────────────────────────────────────────────────────

class S4Skids:
    """S4 Skids agent — Find L0 primitives.

    Detects, catalogs, searches, and deduplicates L0 primitives from
    raw material.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._catalogs: dict[str, Catalog] = {}
        self._indices: dict[str, CatalogIndex] = {}

    # ── Detect ─────────────────────────────────────────────────────

    def detect_primitives(
        self,
        content: str,
        min_size: int = 20,
        max_size: int = 500,
    ) -> dict[str, Any]:
        """Detect L0 primitives from content."""
        primitives, errors = step_detect(content, min_size, max_size)
        return {
            "primitives": [p.to_dict() for p in primitives],
            "total": len(primitives),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Catalog ────────────────────────────────────────────────────

    def catalog_primitives(
        self,
        primitives_data: list[dict[str, Any]],
        catalog_name: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Catalog primitives into a searchable index."""
        primitives = [Primitive.from_dict(p) for p in primitives_data]
        catalog, index, errors = step_catalog(primitives, catalog_name, tags)
        self._catalogs[catalog_name] = catalog
        self._indices[catalog_name] = index
        return {
            "catalog": catalog.to_dict(),
            "index": {
                "keywords": len(index.keywords),
                "types": {t: len(ids) for t, ids in index.by_type.items()},
                "by_type": {t: sorted(ids) for t, ids in index.by_type.items()},
            },
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Search ─────────────────────────────────────────────────────

    def search_primitives(
        self,
        query: str,
        catalog_name: str,
        type_filter: str | None = None,
        min_confidence: float | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search primitives in a catalog."""
        if catalog_name not in self._catalogs:
            return {
                "query": query,
                "catalog": catalog_name,
                "results": [],
                "total": 0,
                "ok": False,
                "errors": [f"Catalog not found: {catalog_name}"],
            }
        catalog = self._catalogs[catalog_name]
        index = self._indices[catalog_name]
        results, errors = step_search(
            catalog, index, query, type_filter, min_confidence, limit
        )
        return {
            "query": query,
            "catalog": catalog_name,
            "results": results,
            "total": len(results),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Dedup ──────────────────────────────────────────────────────

    def dedup_primitives(
        self,
        catalog_names: list[str] | None = None,
        similarity_threshold: float = 0.9,
        keep_strategy: str = "highest_confidence",
    ) -> dict[str, Any]:
        """Deduplicate primitives across catalogs."""
        if catalog_names is None:
            catalog_names = list(self._catalogs.keys())

        catalogs_subset = {name: self._catalogs[name] for name in catalog_names if name in self._catalogs}
        indices_subset = {name: self._indices[name] for name in catalog_names if name in self._indices}

        summary, errors = step_dedup(
            catalogs_subset, indices_subset, similarity_threshold, keep_strategy
        )
        return {
            **summary,
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Skids statistics."""
        total_primitives = sum(len(c.primitives) for c in self._catalogs.values())
        type_counts: dict[str, int] = {}
        for catalog in self._catalogs.values():
            for p in catalog.primitives.values():
                type_counts[p.type] = type_counts.get(p.type, 0) + 1
        return {
            "total_catalogs": len(self._catalogs),
            "total_primitives": total_primitives,
            "by_type": type_counts,
            "catalogs": {name: len(c.primitives) for name, c in self._catalogs.items()},
        }

    # ── Persistence ────────────────────────────────────────────────

    def save_to_vault(self, apply: bool = False) -> str | None:
        """Save skids to vault as JSON (if --apply / vault configured)."""
        if not self.vault_path or not apply:
            return None

        dir_path = self.vault_path / "02-Areas" / "Skills"
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {
            "catalogs": {
                name: {
                    "name": c.name,
                    "created_at": c.created_at,
                    "tags": c.tags,
                    "primitives": {pid: p.to_dict() for pid, p in c.primitives.items()},
                }
                for name, c in self._catalogs.items()
            },
            "stats": self.stats(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        path = dir_path / "skids-primitives.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def load_from_vault(self) -> bool:
        """Load skids from vault JSON file."""
        if not self.vault_path:
            return False

        path = self.vault_path / "02-Areas" / "Skills" / "skids-primitives.json"
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for name, cdata in data.get("catalogs", {}).items():
                catalog = Catalog(
                    name=cdata["name"],
                    created_at=cdata["created_at"],
                    tags=cdata.get("tags", []),
                )
                for pid, pdata in cdata.get("primitives", {}).items():
                    catalog.primitives[pid] = Primitive.from_dict(pdata)
                self._catalogs[name] = catalog

                # Rebuild index
                index = CatalogIndex()
                for pid, p in catalog.primitives.items():
                    words = set(re.findall(r"\w+", p.text.lower()))
                    for w in words:
                        index.keywords.setdefault(w, set()).add(pid)
                    index.by_type.setdefault(p.type, set()).add(pid)
                self._indices[name] = index

            return True
        except (json.JSONDecodeError, TypeError, KeyError):
            return False


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S4 Skids — Find L0 primitives",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")

    sub = parser.add_subparsers(dest="command")

    # detect
    p_detect = sub.add_parser("detect", help="Detect L0 primitives from content")
    p_detect.add_argument("--content", required=True, help="Content to analyze")
    p_detect.add_argument("--min-size", type=int, default=20, help="Minimum primitive size")
    p_detect.add_argument("--max-size", type=int, default=500, help="Maximum primitive size")

    # catalog
    p_catalog = sub.add_parser("catalog", help="Catalog primitives into searchable index")
    p_catalog.add_argument("--catalog", required=True, help="Catalog name")
    p_catalog.add_argument(
        "--primitives-json", required=True, help="JSON file with primitives list"
    )
    p_catalog.add_argument("--tags", default="", help="Comma-separated tags")

    # search
    p_search = sub.add_parser("search", help="Search primitives in a catalog")
    p_search.add_argument("--catalog", required=True, help="Catalog name")
    p_search.add_argument("--query", required=True, help="Search query")
    p_search.add_argument("--type-filter", help="Filter by primitive type")
    p_search.add_argument("--min-confidence", type=float, help="Minimum confidence (0.0-1.0)")
    p_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # dedup
    p_dedup = sub.add_parser("dedup", help="Deduplicate primitives across catalogs")
    p_dedup.add_argument(
        "--catalogs", help="Comma-separated catalog names (default: all)"
    )
    p_dedup.add_argument(
        "--similarity-threshold", type=float, default=0.9, help="Similarity threshold"
    )
    p_dedup.add_argument(
        "--keep-strategy",
        default="highest_confidence",
        choices=["highest_confidence", "first_seen"],
        help="Keep strategy (default: highest_confidence)",
    )

    # stats
    sub.add_parser("stats", help="Show skids statistics")

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
    print("Borg S4 Skids — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Detect primitives
    print("\n[1/7] Detect primitives...")
    skids = S4Skids()
    result = skids.detect_primitives(
        "The pipeline processes data. Decide on the architecture. "
        "What is the failure mode? Warning: check the logs. "
        "See the documentation for details."
    )
    assert result["ok"], f"Detect failed: {result['errors']}"
    assert result["total"] > 0, "Should detect at least one primitive"
    print(f"  ✅ Detected {result['total']} primitives")
    passed += 1

    # Test 2: Catalog primitives
    print("\n[2/7] Catalog primitives...")
    result = skids.catalog_primitives(
        result["primitives"],
        catalog_name="test-catalog",
        tags=["test"],
    )
    assert result["ok"], f"Catalog failed: {result['errors']}"
    assert result["catalog"]["total_primitives"] == result["catalog"]["total_primitives"]
    print(f"  ✅ Cataloged {result['catalog']['total_primitives']} primitives")
    passed += 1

    # Test 3: Search primitives
    print("\n[3/7] Search primitives...")
    result = skids.search_primitives(
        query="pipeline data",
        catalog_name="test-catalog",
    )
    assert result["ok"], f"Search failed: {result['errors']}"
    print(f"  ✅ Search: {result['total']} results for 'pipeline data'")
    passed += 1

    # Test 4: Search with type filter
    print("\n[4/7] Search with type filter...")
    result = skids.search_primitives(
        query="",
        catalog_name="test-catalog",
        type_filter="warning",
    )
    assert result["ok"], f"Type filter search failed: {result['errors']}"
    print(f"  ✅ Type filter: {result['total']} warning primitives")
    passed += 1

    # Test 5: Dedup
    print("\n[5/7] Dedup primitives...")
    # Add a duplicate catalog
    skids.catalog_primitives(
        skids.detect_primitives(
            "The pipeline processes data. Decide on the architecture."
        )["primitives"],
        catalog_name="test-catalog-2",
    )
    result = skids.dedup_primitives(
        catalog_names=["test-catalog", "test-catalog-2"],
        similarity_threshold=0.9,
    )
    assert result["ok"], f"Dedup failed: {result['errors']}"
    print(f"  ✅ Dedup: removed {result['duplicates_removed']} duplicates")
    passed += 1

    # Test 6: Stats
    print("\n[6/7] Stats...")
    stats = skids.stats()
    assert stats["total_catalogs"] >= 1
    assert stats["total_primitives"] >= 1
    print(f"  ✅ Stats: {stats['total_catalogs']} catalogs, {stats['total_primitives']} primitives")
    passed += 1

    # Test 7: Similarity function
    print("\n[7/7] Similarity function...")
    sim = _jaccard_similarity("hello world", "hello world")
    assert sim == 1.0, f"Identical strings should have similarity 1.0, got {sim}"
    sim2 = _jaccard_similarity("hello world", "goodbye mars")
    assert sim2 == 0.0, f"Completely different strings should have similarity 0.0, got {sim2}"
    print(f"  ✅ Similarity: identical=1.0, different=0.0")
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

    skids = S4Skids(vault_path=args.vault)
    skids.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.command == "detect":
        result = skids.detect_primitives(
            args.content,
            min_size=args.min_size,
            max_size=args.max_size,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "catalog":
        with open(args.primitives_json) as f:
            primitives_data = json.load(f)
        if isinstance(primitives_data, dict) and "primitives" in primitives_data:
            primitives_data = primitives_data["primitives"]
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        result = skids.catalog_primitives(
            primitives_data,
            catalog_name=args.catalog,
            tags=tags,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = skids.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "search":
        result = skids.search_primitives(
            query=args.query,
            catalog_name=args.catalog,
            type_filter=args.type_filter,
            min_confidence=args.min_confidence,
            limit=args.limit,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "dedup":
        catalog_names = None
        if args.catalogs:
            catalog_names = [c.strip() for c in args.catalogs.split(",") if c.strip()]
        result = skids.dedup_primitives(
            catalog_names=catalog_names,
            similarity_threshold=args.similarity_threshold,
            keep_strategy=args.keep_strategy,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = skids.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "stats":
        stats = skids.stats()
        print(json.dumps(stats, indent=2))
        return 0

    print("No action given. Run with --help to see the options.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
