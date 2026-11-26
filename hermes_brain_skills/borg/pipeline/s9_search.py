"""Borg — Phase 2: S9 Search Agent.

Per mem-draft-spec.txt §4 (Pipeline S9):
S9 Search — Retrieval + routing.

Retrieves relevant records from the knowledge base, routes queries to
appropriate targets, ranks and re-ranks results, and caches results for
fast repeated queries.

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
import math
import time


# ── Sub-prompt loading ───────────────────────────────────────────────────
_cli_dir = Path(__file__).resolve().parent
_prompts_dir = _cli_dir / "prompts"


def _load_prompt_file(name: str) -> str:
    path = _prompts_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


S9_RETRIEVAL_PROMPT = _load_prompt_file("s9_retrieval_prompt")
S9_ROUTING_PROMPT = _load_prompt_file("s9_routing_prompt")
S9_RESULT_RANK_PROMPT = _load_prompt_file("s9_result_rank_prompt")
S9_CACHE_PROMPT = _load_prompt_file("s9_cache_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Types ────────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """A single search result."""

    record_id: str
    record_type: str
    title: str
    content: str
    relevance_score: float
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    adjusted_score: float | None = None
    rank: int | None = None
    ranking_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "title": self.title,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "source": self.source,
            "metadata": dict(self.metadata),
            "adjusted_score": self.adjusted_score,
            "rank": self.rank,
            "ranking_factors": list(self.ranking_factors),
        }


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""

    query: str
    catalogs_searched: list[str]
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "catalogs_searched": list(self.catalogs_searched),
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "ok": self.ok,
            "errors": list(self.errors),
        }


@dataclass
class RoutingResult:
    """Result of routing a query."""

    query: str
    query_type: str
    primary_target: str
    secondary_targets: list[str] = field(default_factory=list)
    routing_confidence: float = 0.0
    rationale: str = ""
    estimated_latency: str = ""
    multi_target: bool = False
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "query_type": self.query_type,
            "primary_target": self.primary_target,
            "secondary_targets": list(self.secondary_targets),
            "routing_confidence": self.routing_confidence,
            "rationale": self.rationale,
            "estimated_latency": self.estimated_latency,
            "multi_target": self.multi_target,
            "ok": self.ok,
            "errors": list(self.errors),
        }


@dataclass
class RankingResult:
    """Result of ranking search results."""

    query: str
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    diversity_applied: bool = False
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "diversity_applied": self.diversity_applied,
            "ok": self.ok,
            "errors": list(self.errors),
        }


@dataclass
class CacheResult:
    """Result of a cache operation."""

    operation: str
    query: str
    cached: bool = False
    results: list[SearchResult] | None = None
    ttl_remaining: float | None = None
    cache_stats: dict[str, Any] | None = None
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "query": self.query,
            "cached": self.cached,
            "results": [r.to_dict() for r in self.results] if self.results else None,
            "ttl_remaining": self.ttl_remaining,
            "cache_stats": dict(self.cache_stats) if self.cache_stats else None,
            "ok": self.ok,
            "errors": list(self.errors),
        }


# ── Helper functions ─────────────────────────────────────────────────────

def _query_id(query: str) -> str:
    """Generate a deterministic query ID."""
    h = hashlib.sha256(query.encode()).hexdigest()[:12]
    return f"s:{h}"


def _char_3grams(text: str) -> set[str]:
    """Generate character 3-grams for text similarity."""
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


def _score_result(
    result: SearchResult,
    query_terms: set[str],
    user_context: dict[str, Any] | None = None,
) -> tuple[float, list[str]]:
    """Score and rank a single search result.

    Returns (adjusted_score, ranking_factors).
    """
    factors: list[str] = []
    score = result.relevance_score

    # Relevance factor
    factors.append(f"relevance:{result.relevance_score:.2f}")

    # Recency factor (if metadata has timestamp)
    if result.metadata.get("timestamp"):
        factors.append("recency:recent")
        score += 0.1

    # Confidence factor
    if result.metadata.get("confidence", 0) > 0.7:
        factors.append("high_confidence")
        score += 0.05

    # User context factor (preferred sources)
    if user_context and "preferred_sources" in user_context:
        if result.source in user_context["preferred_sources"]:
            factors.append("preferred_source")
            score += 0.1

    # Query term match bonus
    content_lower = result.content.lower()
    title_lower = result.title.lower()
    matched_terms = sum(1 for t in query_terms if t in content_lower or t in title_lower)
    if matched_terms > 0:
        factors.append(f"term_match:{matched_terms}")
        score += min(matched_terms * 0.05, 0.2)

    return min(score, 1.0), factors


# ── Step 1: Retrieval ────────────────────────────────────────────────────

def step_retrieve(
    query: str,
    records: list[dict[str, Any]],
    catalogs: list[str] | None = None,
    filters: dict[str, Any] | None = None,
    top_k: int = 10,
    min_score: float = 0.0,
) -> tuple[RetrievalResult, list[str]]:
    """Retrieve relevant records from the knowledge base.

    Returns (retrieval_result, errors).
    """
    errors: list[str] = []
    catalogs = catalogs or ["vault"]
    filters = filters or {}

    query_terms = set(query.lower().split())
    scored_results: list[tuple[SearchResult, float]] = []

    for rec in records:
        # Apply filters
        skip = False
        for filter_key, filter_val in filters.items():
            if rec.get(filter_key) != filter_val:
                skip = True
                break
        if skip:
            continue

        # Compute relevance
        title = rec.get("title", rec.get("id", ""))
        content = rec.get("content", rec.get("text", ""))
        source = rec.get("source", rec.get("catalog", "vault"))

        title_sim = _jaccard_similarity(query, title)
        content_sim = _jaccard_similarity(query, content)
        relevance = max(title_sim * 0.6 + content_sim * 0.4, 0.0)

        if relevance < min_score:
            continue

        result = SearchResult(
            record_id=rec.get("id", rec.get("record_id", "")),
            record_type=rec.get("type", rec.get("record_type", "unknown")),
            title=title,
            content=content[:500],  # Snippet
            relevance_score=round(relevance, 4),
            source=source,
            metadata={k: v for k, v in rec.items() if k not in ("id", "title", "content", "text", "source", "catalog")},
        )
        scored_results.append((result, relevance))

    # Sort by relevance descending
    scored_results.sort(key=lambda x: x[1], reverse=True)
    scored_results = scored_results[:top_k]

    results = [r for r, _ in scored_results]

    return RetrievalResult(
        query=query,
        catalogs_searched=catalogs,
        results=results,
        total=len(results),
        ok=True,
        errors=errors,
    ), errors


# ── Step 2: Routing ──────────────────────────────────────────────────────

def step_route(
    query: str,
    query_type: str = "exploration",
    context: str = "",
    available_targets: list[str] | None = None,
) -> tuple[RoutingResult, list[str]]:
    """Route a search query to the appropriate target.

    Returns (routing_result, errors).
    """
    errors: list[str] = []
    available_targets = available_targets or ["vault", "skills", "archive"]

    # Determine query type from content if not specified
    query_lower = query.lower()
    if any(w in query_lower for w in ["what is", "define", "meaning of"]):
        query_type = "fact_lookup"
    elif any(w in query_lower for w in ["research", "deep dive", "investigate"]):
        query_type = "deep_research"
    elif any(w in query_lower for w in ["compare", "vs", "versus", "difference"]):
        query_type = "comparison"
    elif any(w in query_lower for w in ["explore", "browse", "discover"]):
        query_type = "exploration"
    elif any(w in query_lower for w in ["find", "locate", "where is"]):
        query_type = "navigation"

    # Route based on type
    if query_type == "fact_lookup":
        primary_target = "skills"
        secondary_targets = ["vault"]
        confidence = 0.85
        latency = "< 1s"
    elif query_type == "deep_research":
        primary_target = "archive"
        secondary_targets = ["skills", "vault"]
        confidence = 0.75
        latency = "5-10s"
    elif query_type == "comparison":
        primary_target = "skills"
        secondary_targets = ["archive", "vault"]
        confidence = 0.8
        latency = "2-3s"
    elif query_type == "navigation":
        primary_target = "vault"
        secondary_targets = ["skills"]
        confidence = 0.9
        latency = "< 1s"
    else:  # exploration
        primary_target = "vault"
        secondary_targets = ["skills", "archive"]
        confidence = 0.7
        latency = "1-2s"

    multi_target = len(secondary_targets) > 0

    return RoutingResult(
        query=query,
        query_type=query_type,
        primary_target=primary_target,
        secondary_targets=secondary_targets,
        routing_confidence=confidence,
        rationale=f"Query type '{query_type}' best served by {primary_target} with {', '.join(secondary_targets)} as secondary",
        estimated_latency=latency,
        multi_target=multi_target,
        ok=True,
        errors=errors,
    ), errors


# ── Step 3: Result Rank ──────────────────────────────────────────────────

def step_rank(
    results: list[SearchResult],
    query: str,
    user_context: dict[str, Any] | None = None,
    diversity: bool = True,
) -> tuple[RankingResult, list[str]]:
    """Rank and re-rank search results.

    Returns (ranking_result, errors).
    """
    errors: list[str] = []
    query_terms = set(query.lower().split())

    # Score each result
    scored: list[tuple[SearchResult, float, list[str]]] = []
    for result in results:
        adjusted_score, factors = _score_result(result, query_terms, user_context)
        result.adjusted_score = adjusted_score
        result.ranking_factors = factors
        scored.append((result, adjusted_score, factors))

    # Sort by adjusted score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Apply diversity filtering
    if diversity and len(scored) > 1:
        diversified: list[tuple[SearchResult, float, list[str]]] = []
        seen_sources: set[str] = set()
        for result, score, factors in scored:
            if result.source not in seen_sources or len(diversified) < 3:
                diversified.append((result, score, factors))
                seen_sources.add(result.source)
        scored = diversified

    # Assign ranks
    for i, (result, score, factors) in enumerate(scored):
        result.rank = i + 1

    final_results = [r for r, _, _ in scored]

    return RankingResult(
        query=query,
        results=final_results,
        total=len(final_results),
        diversity_applied=diversity,
        ok=True,
        errors=errors,
    ), errors


# ── Step 4: Cache ────────────────────────────────────────────────────────

def step_cache(
    operation: str,
    query: str,
    results: list[SearchResult] | None = None,
    cache_ttl: int = 3600,
    cache_store: dict[str, Any] | None = None,
) -> tuple[CacheResult, list[str]]:
    """Manage search result cache.

    Returns (cache_result, errors).
    """
    errors: list[str] = []
    if cache_store is None:
        cache_store = {}

    now = time.time()

    if operation == "store":
        if results is None:
            errors.append("Results required for store operation")
            return CacheResult(operation="store", query=query, ok=False, errors=errors), errors

        # Convert dict results to SearchResult objects if needed
        result_objs = []
        for r in results:
            if isinstance(r, SearchResult):
                result_objs.append(r)
            else:
                result_objs.append(SearchResult(
                    record_id=r.get("record_id", ""),
                    record_type=r.get("record_type", "unknown"),
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    relevance_score=r.get("relevance_score", 0.0),
                    source=r.get("source", "unknown"),
                    metadata=r.get("metadata", {}),
                ))

        cache_store[query] = {
            "results": [r.to_dict() for r in result_objs],
            "ttl": cache_ttl,
            "stored_at": now,
        }
        return CacheResult(
            operation="store",
            query=query,
            cached=True,
            ok=True,
            errors=errors,
        ), errors

    elif operation == "retrieve":
        if query in cache_store:
            entry = cache_store[query]
            ttl_remaining = entry["stored_at"] + entry["ttl"] - now
            if ttl_remaining > 0:
                cached_results = [SearchResult(**r) for r in entry["results"]]
                return CacheResult(
                    operation="retrieve",
                    query=query,
                    cached=True,
                    results=cached_results,
                    ttl_remaining=round(ttl_remaining, 1),
                    ok=True,
                    errors=errors,
                ), errors
            else:
                # Expired
                del cache_store[query]
                return CacheResult(
                    operation="retrieve",
                    query=query,
                    cached=False,
                    ok=True,
                    errors=errors,
                ), errors
        else:
            return CacheResult(
                operation="retrieve",
                query=query,
                cached=False,
                ok=True,
                errors=errors,
            ), errors

    elif operation == "invalidate":
        if query in cache_store:
            del cache_store[query]
        return CacheResult(
            operation="invalidate",
            query=query,
            cached=False,
            ok=True,
            errors=errors,
        ), errors

    elif operation == "stats":
        total_entries = len(cache_store)
        expired = sum(
            1 for v in cache_store.values()
            if v["stored_at"] + v["ttl"] - now <= 0
        )
        hit_rate = 0.5  # Placeholder - would need hit/miss tracking
        return CacheResult(
            operation="stats",
            query=query,
            cached=False,
            cache_stats={
                "total_entries": total_entries,
                "hit_rate": hit_rate,
                "expired_entries": expired,
            },
            ok=True,
            errors=errors,
        ), errors

    else:
        errors.append(f"Unknown cache operation: {operation}")
        return CacheResult(
            operation=operation,
            query=query,
            ok=False,
            errors=errors,
        ), errors


# ── S9 Search Agent ─────────────────────────────────────────────────────

class S9Search:
    """S9 Search agent — Retrieval + routing.

    Retrieves records, routes queries, ranks results, and caches for
    fast repeated queries.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._cache: dict[str, Any] = {}
        self._records: list[dict[str, Any]] = []

    # ── Retrieve ─────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        catalogs: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> dict[str, Any]:
        """Retrieve relevant records from the knowledge base."""
        result, errors = step_retrieve(
            query, self._records, catalogs, filters, top_k, min_score
        )
        return result.to_dict()

    # ── Route ────────────────────────────────────────────────────────

    def route(
        self,
        query: str,
        query_type: str = "exploration",
        context: str = "",
        available_targets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Route a search query to the appropriate target."""
        result, errors = step_route(
            query, query_type, context, available_targets
        )
        return result.to_dict()

    # ── Rank ─────────────────────────────────────────────────────────

    def rank(
        self,
        results: list[dict[str, Any]],
        query: str,
        user_context: dict[str, Any] | None = None,
        diversity: bool = True,
    ) -> dict[str, Any]:
        """Rank and re-rank search results."""
        search_results = [
            SearchResult(
                record_id=r.get("record_id", ""),
                record_type=r.get("record_type", "unknown"),
                title=r.get("title", ""),
                content=r.get("content", ""),
                relevance_score=r.get("relevance_score", 0.0),
                source=r.get("source", "unknown"),
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]
        result, errors = step_rank(search_results, query, user_context, diversity)
        return result.to_dict()

    # ── Cache ────────────────────────────────────────────────────────

    def cache(
        self,
        operation: str,
        query: str,
        results: list[dict[str, Any]] | None = None,
        cache_ttl: int = 3600,
    ) -> dict[str, Any]:
        """Manage search result cache."""
        search_results = None
        if results:
            search_results = [
                SearchResult(
                    record_id=r.get("record_id", ""),
                    record_type=r.get("record_type", "unknown"),
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    relevance_score=r.get("relevance_score", 0.0),
                    source=r.get("source", "unknown"),
                    metadata=r.get("metadata", {}),
                )
                for r in results
            ]
        result, errors = step_cache(
            operation, query, search_results, cache_ttl, self._cache
        )
        return result.to_dict()

    # ── Records ──────────────────────────────────────────────────────

    def load_records(self, records: list[dict[str, Any]]) -> None:
        """Load records into the search index."""
        self._records = records

    def get_records(self) -> list[dict[str, Any]]:
        """Get all loaded records."""
        return list(self._records)

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Search statistics."""
        return {
            "total_records": len(self._records),
            "cache_entries": len(self._cache),
            "cache_expired": sum(
                1 for v in self._cache.values()
                if v["stored_at"] + v["ttl"] - time.time() <= 0
            ),
        }

    # ── Persistence ────────────────────────────────────────────────

    def save_to_vault(self, apply: bool = False) -> str | None:
        """Save search data to vault as JSON (if --apply / vault configured)."""
        if not self.vault_path or not apply:
            return None

        dir_path = self.vault_path / "02-Areas" / "Skills"
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {
            "records": self._records,
            "cache": self._cache,
            "stats": self.stats(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        path = dir_path / "search-results.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def load_from_vault(self) -> bool:
        """Load search data from vault JSON file."""
        if not self.vault_path:
            return False

        path = self.vault_path / "02-Areas" / "Skills" / "search-results.json"
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._records = data.get("records", [])
            self._cache = data.get("cache", {})
            return True
        except (json.JSONDecodeError, TypeError, KeyError):
            return False


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S9 Search — Retrieval + routing",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")

    sub = parser.add_subparsers(dest="command")

    # retrieve
    p_retrieve = sub.add_parser("retrieve", help="Retrieve relevant records")
    p_retrieve.add_argument("--query", required=True, help="Search query")
    p_retrieve.add_argument(
        "--catalogs", default="", help="Comma-separated catalog names"
    )
    p_retrieve.add_argument(
        "--filters", default="", help="JSON string for filters"
    )
    p_retrieve.add_argument("--top-k", type=int, default=10, help="Max results")
    p_retrieve.add_argument(
        "--min-score", type=float, default=0.0, help="Minimum relevance score"
    )

    # route
    p_route = sub.add_parser("route", help="Route a search query")
    p_route.add_argument("--query", required=True, help="Search query")
    p_route.add_argument(
        "--query-type", default="exploration", help="Type of query"
    )
    p_route.add_argument("--context", default="", help="Additional context")
    p_route.add_argument(
        "--targets", default="", help="Comma-separated available targets"
    )

    # rank
    p_rank = sub.add_parser("rank", help="Rank and re-rank results")
    p_rank.add_argument("--query", required=True, help="Search query")
    p_rank.add_argument(
        "--results-json", required=True, help="JSON file with results list"
    )
    p_rank.add_argument(
        "--user-context", default="", help="JSON string for user context"
    )
    p_rank.add_argument(
        "--no-diversity", action="store_true", help="Disable diversity filtering"
    )

    # cache
    p_cache = sub.add_parser("cache", help="Manage search result cache")
    p_cache.add_argument(
        "--operation", required=True, help="store|retrieve|invalidate|stats"
    )
    p_cache.add_argument("--query", required=True, help="Query string")
    p_cache.add_argument(
        "--results-json", help="JSON file with results to store"
    )
    p_cache.add_argument(
        "--cache-ttl", type=int, default=3600, help="Cache TTL in seconds"
    )

    # stats
    sub.add_parser("stats", help="Show search statistics")

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
    print("Borg S9 Search — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Retrieve
    print("\n[1/6] Retrieve records...")
    search = S9Search()
    search.load_records([
        {"id": "r1", "title": "Python Programming Guide", "content": "Learn Python programming with examples", "type": "tutorial", "source": "docs", "confidence": 0.9},
        {"id": "r2", "title": "SQL Database Design", "content": "Design relational databases with SQL", "type": "tutorial", "source": "docs", "confidence": 0.85},
        {"id": "r3", "title": "Python Web Development", "content": "Build web apps with Python and Flask", "type": "tutorial", "source": "blog", "confidence": 0.8},
    ])
    result = search.retrieve("python programming", top_k=5)
    assert result["ok"], f"Retrieve failed: {result['errors']}"
    assert result["total"] > 0
    assert result["results"][0]["relevance_score"] > 0
    print(f"  ✅ Retrieved: {result['total']} results")
    passed += 1

    # Test 2: Route
    print("\n[2/6] Route query...")
    result = search.route(
        query="What is Python programming?",
        query_type="fact_lookup",
        available_targets=["vault", "skills", "archive"],
    )
    assert result["ok"], f"Route failed: {result['errors']}"
    assert result["query_type"] in ("fact_lookup", "deep_research", "comparison", "exploration", "navigation")
    print(f"  ✅ Routed: {result['query_type']} → {result['primary_target']}")
    passed += 1

    # Test 3: Rank
    print("\n[3/6] Rank results...")
    results = [
        {"record_id": "r1", "record_type": "tutorial", "title": "Python Programming Guide", "content": "Learn Python programming with examples", "relevance_score": 0.9, "source": "docs"},
        {"record_id": "r2", "record_type": "tutorial", "title": "SQL Database Design", "content": "Design relational databases with SQL", "relevance_score": 0.5, "source": "docs"},
    ]
    result = search.rank(results, "python programming", diversity=True)
    assert result["ok"], f"Rank failed: {result['errors']}"
    assert result["results"][0]["rank"] == 1
    print(f"  ✅ Ranked: {result['total']} results, diversity={result['diversity_applied']}")
    passed += 1

    # Test 4: Cache store
    print("\n[4/6] Cache store...")
    result = search.cache(
        operation="store",
        query="test query",
        results=[{"record_id": "r1", "record_type": "tutorial", "title": "Test", "content": "Test content", "relevance_score": 0.9, "source": "test"}],
        cache_ttl=3600,
    )
    assert result["ok"], f"Cache store failed: {result['errors']}"
    assert result["cached"] == True
    print(f"  ✅ Cache stored: {result['operation']}")
    passed += 1

    # Test 5: Cache retrieve
    print("\n[5/6] Cache retrieve...")
    result = search.cache(
        operation="retrieve",
        query="test query",
    )
    assert result["ok"], f"Cache retrieve failed: {result['errors']}"
    assert result["cached"] == True
    assert result["results"] is not None
    assert len(result["results"]) == 1
    print(f"  ✅ Cache retrieved: {result['cached']}, ttl_remaining={result['ttl_remaining']}s")
    passed += 1

    # Test 6: Stats
    print("\n[6/6] Stats...")
    stats = search.stats()
    assert "total_records" in stats
    assert stats["total_records"] == 3
    print(f"  ✅ Stats: {stats['total_records']} records, {stats['cache_entries']} cache entries")
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

    search = S9Search(vault_path=args.vault)
    search.load_from_vault()

    dry_run = args.dry_run and not args.apply

    import json as _json

    if args.command == "retrieve":
        catalogs = [c.strip() for c in args.catalogs.split(",") if c.strip()] or None
        filters = _json.loads(args.filters) if args.filters else None
        result = search.retrieve(
            query=args.query,
            catalogs=catalogs,
            filters=filters,
            top_k=args.top_k,
            min_score=args.min_score,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = search.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "route":
        targets = [t.strip() for t in args.targets.split(",") if c.strip() for c in [args.targets]] if args.targets else None
        result = search.route(
            query=args.query,
            query_type=args.query_type,
            context=args.context,
            available_targets=targets,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = search.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "rank":
        with open(args.results_json) as f:
            results = _json.load(f)
        user_context = _json.loads(args.user_context) if args.user_context else None
        result = search.rank(
            results=results,
            query=args.query,
            user_context=user_context,
            diversity=not args.no_diversity,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = search.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "cache":
        results = None
        if args.results_json:
            with open(args.results_json) as f:
                results = _json.load(f)
        result = search.cache(
            operation=args.operation,
            query=args.query,
            results=results,
            cache_ttl=args.cache_ttl,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = search.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "stats":
        stats = search.stats()
        print(_json.dumps(stats, indent=2))
        return 0

    print("No action given. Run with --help to see the options.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
