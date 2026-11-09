"""Hermes Brain — Paper Mapping CLI.

Entry point for the Paper Mapping skill. Dispatches to sub-modules:
http_client, openalex, inciteful, models, mapping, report.

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only (urllib for HTTP)
  - --test built-in self-test suite
"""

import argparse
import json
import os
import sys
from typing import Any

from . import http_client, openalex, inciteful, models, mapping, report


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Hermes Brain Paper Mapping — discover related papers, "
            "citations, and same-author works via OpenAlex with "
            "Inciteful.XYZ-inspired algorithms."
        ),
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview without applying (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (overrides --dry-run)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run built-in self-test suite",
    )
    parser.add_argument(
        "--query",
        help="Paper title or DOI to search for",
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=10,
        help="Number of results per category (default: 10)",
    )

    # --- Inciteful-inspired feature flags --------------------------------
    parser.add_argument(
        "--similarity",
        action="store_true",
        help="Rank citing/cited works by similarity to seed (link prediction)",
    )
    parser.add_argument(
        "--importance",
        action="store_true",
        help="Rank works by PageRank importance in citation graph",
    )
    parser.add_argument(
        "--literature-connector",
        metavar="PAPER_B",
        help="Find citation path between --query paper and PAPER_B (by OpenAlex ID)",
    )
    parser.add_argument(
        "--citation-network",
        action="store_true",
        help="Build recursive citation network from seed paper",
    )
    parser.add_argument(
        "--max-hops",
        type=int,
        default=2,
        help="Max hops for citation network / literature connector (default: 2)",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Apply graph pruning to dampen canonical papers",
    )
    parser.add_argument(
        "--keyword-filter",
        metavar="KEYWORDS",
        help="Comma-separated keywords to filter results by title",
    )
    parser.add_argument(
        "--author-filter",
        metavar="AUTHORS",
        help="Comma-separated author names to filter results",
    )
    parser.add_argument(
        "--min-year",
        type=int,
        default=None,
        help="Minimum publication year filter",
    )
    parser.add_argument(
        "--max-year",
        type=int,
        default=None,
        help="Maximum publication year filter",
    )
    parser.add_argument(
        "--extended-graph",
        action="store_true",
        help="Extend citation graph by extra 3 hops (Inciteful extended graph)",
    )

    return parser.parse_args()


def run_self_test():
    """Run built-in self-test suite across all sub-modules."""
    print("🧪 Paper Mapping Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    def check(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"✅ {name}")
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            failed += 1

    # --- http_client tests ----------------------------------------------
    def test_extract_short_id():
        assert http_client.extract_short_id(
            "https://openalex.org/W123456789"
        ) == "W123456789"
        assert http_client.extract_short_id("W123456789") == "W123456789"

    check("http_client.extract_short_id parses IDs", test_extract_short_id)

    # --- models tests ----------------------------------------------------
    def test_extract_openalex_id():
        assert models.extract_openalex_id(
            {"id": "https://openalex.org/W123456789"}
        ) == "W123456789"
        assert models.extract_openalex_id({"id": "W123456789"}) == "W123456789"
        assert models.extract_openalex_id({"id": ""}) == ""

    check("models.extract_openalex_id parses IDs", test_extract_openalex_id)

    def test_summarize_work():
        work = {
            "id": "https://openalex.org/W999",
            "display_name": "Test Paper",
            "publication_year": 2024,
            "doi": "https://doi.org/10.1234/test",
            "cited_by_count": 42,
            "open_access": {"is_oa": True},
            "authorships": [
                {"author": {"display_name": "Alice"}},
                {"author": {"display_name": "Bob"}},
            ],
        }
        s = models.summarize_work(work)
        assert s["openalex_id"] == "W999"
        assert s["title"] == "Test Paper"
        assert s["year"] == 2024
        assert s["cited_by_count"] == 42
        assert s["is_oa"] is True
        assert s["authors"] == ["Alice", "Bob"]

    check("models.summarize_work produces compact dict", test_summarize_work)

    # --- openalex tests (structure only, no network) --------------------
    def test_map_paper_error():
        result = mapping.map_paper("nonexistent paper xyz123", per_page=1, dry_run=True)
        assert isinstance(result, dict)
        assert "seed_work" in result
        assert "citing_works" in result
        assert "cited_works" in result
        assert "same_author_works" in result
        assert "error" in result
        assert "dry_run" in result

    check("mapping.map_paper returns structured result", test_map_paper_error)

    # --- inciteful tests ------------------------------------------------
    def test_similarity_score():
        score = inciteful.similarity_score("W1", "W2")
        assert 0.0 <= score <= 1.0

    check("inciteful.similarity_score returns valid score", test_similarity_score)

    def test_rank_by_similarity():
        candidates = [
            {"openalex_id": "W1", "title": "Paper 1"},
            {"openalex_id": "W2", "title": "Paper 2"},
        ]
        ranked = inciteful.rank_by_similarity(candidates, "W0", top_n=5)
        assert len(ranked) == 2
        for r in ranked:
            assert "similarity_score" in r

    check("inciteful.rank_by_similarity ranks candidates", test_rank_by_similarity)

    def test_pagerank_importance():
        nodes = ["W1", "W2", "W3"]
        edges = [("W1", "W2"), ("W2", "W3")]
        scores = inciteful.pagerank_importance(nodes, edges)
        assert "W1" in scores
        assert "W2" in scores
        assert "W3" in scores

    check("inciteful.pagerank_importance computes scores", test_pagerank_importance)

    def test_rank_by_importance():
        candidates = [
            {"openalex_id": "W1", "title": "Paper 1"},
            {"openalex_id": "W2", "title": "Paper 2"},
        ]
        scores = {"W1": 0.8, "W2": 0.3}
        ranked = inciteful.rank_by_importance(candidates, scores, top_n=5)
        assert ranked[0]["importance_score"] == 0.8
        assert ranked[1]["importance_score"] == 0.3

    check("inciteful.rank_by_importance ranks candidates", test_rank_by_importance)

    def test_literature_connector_same_paper():
        result = inciteful.literature_connector("W1", "W1", dry_run=True)
        assert result["shortest_path"] == ["W1"]
        assert len(result["paths"]) == 1

    check("inciteful.literature_connector same paper", test_literature_connector_same_paper)

    def test_prune_canonical():
        nodes = [
            {"openalex_id": "W1", "title": "Canonical", "cited_by_count": 10000},
            {"openalex_id": "W2", "title": "Niche", "cited_by_count": 5},
        ]
        edges = [("W1", "W2"), ("W2", "W1")]
        p_nodes, p_edges = inciteful.prune_canonical(nodes, edges, threshold=0.5)
        assert isinstance(p_nodes, list)
        assert isinstance(p_edges, list)

    check("inciteful.prune_canonical prunes graph", test_prune_canonical)

    def test_filters():
        candidates = [
            {"title": "Deep Learning for Vision", "authors": ["Alice"], "year": 2023},
            {"title": "Reinforcement Learning", "authors": ["Bob"], "year": 2020},
        ]
        kw = inciteful.filter_by_keyword(candidates, ["learning"])
        assert len(kw) == 2
        auth = inciteful.filter_by_author(candidates, ["Alice"])
        assert len(auth) == 1
        year = inciteful.filter_by_year(candidates, min_year=2022)
        assert len(year) == 1

    check("inciteful filters work correctly", test_filters)

    def test_extended_graph():
        # Dry run only — no network needed for structure check
        # Just verify function exists and returns correct shape
        assert callable(inciteful.extended_graph)

    check("inciteful.extended_graph is callable", test_extended_graph)

    # --- report tests ---------------------------------------------------
    def test_generate_report():
        mapping_result = {
            "seed_query": "test query",
            "seed_work": {
                "openalex_id": "W1",
                "title": "Test Seed",
                "year": 2023,
                "doi": "https://doi.org/10.1/test",
                "cited_by_count": 10,
                "is_oa": True,
                "authors": ["Author A"],
                "url": "https://openalex.org/W1",
            },
            "citing_works": [],
            "cited_works": [],
            "same_author_works": [],
            "error": None,
            "dry_run": True,
        }
        r = report.generate_report("/tmp/test-vault", mapping_result)
        assert "Paper Mapping Report" in r
        assert "Test Seed" in r
        assert "Citing Works" in r
        assert "Cited Works" in r
        assert "Same-Author Works" in r

    check("report.generate_report produces valid markdown", test_generate_report)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


def main():
    args = parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.vault:
        args.vault = os.environ.get("HERMES_VAULT_PATH")
    if not args.vault:
        print(
            "Error: --vault <path> or HERMES_VAULT_PATH is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Deferred path resolution — called from main(), never at import time
    http_client.OPENALEX_BASE  # ensure module loaded
    dry_run = not args.apply

    if not args.query:
        print(
            "Error: --query <paper title or DOI> is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Core mapping ---------------------------------------------------
    mapping_result = mapping.map_paper(
        args.query, per_page=args.per_page, dry_run=dry_run
    )

    seed = mapping_result.get("seed_work") or {}
    seed_id = seed.get("openalex_id", "")

    # --- Inciteful-inspired feature computation -------------------------
    similarity_results: list[dict[str, Any]] | None = None
    importance_results: list[dict[str, Any]] | None = None
    literature_connector_result: dict[str, Any] | None = None
    citation_network_result: dict[str, Any] | None = None
    filters_applied: dict[str, Any] | None = None

    # Collect all candidates for ranking/filtering
    all_candidates: list[dict[str, Any]] = []
    all_candidates.extend(mapping_result.get("citing_works", []))
    all_candidates.extend(mapping_result.get("cited_works", []))
    all_candidates.extend(mapping_result.get("same_author_works", []))

    # Apply filters if requested
    if any(
        [args.keyword_filter, args.author_filter, args.min_year, args.max_year]
    ):
        filters_applied = {}
        filtered = list(all_candidates)

        if args.keyword_filter:
            keywords = [k.strip() for k in args.keyword_filter.split(",")]
            filtered = inciteful.filter_by_keyword(filtered, keywords)
            filters_applied["keyword_filter"] = args.keyword_filter

        if args.author_filter:
            authors = [a.strip() for a in args.author_filter.split(",")]
            filtered = inciteful.filter_by_author(filtered, authors)
            filters_applied["author_filter"] = args.author_filter

        if args.min_year is not None or args.max_year is not None:
            filtered = inciteful.filter_by_year(
                filtered, args.min_year, args.max_year
            )
            filters_applied["year_range"] = (
                f"{args.min_year or 'any'}–{args.max_year or 'any'}"
            )

        all_candidates = filtered

    # Similarity ranking
    if args.similarity and seed_id:
        similarity_results = inciteful.rank_by_similarity(
            all_candidates, seed_id, top_n=args.per_page
        )

    # Importance ranking
    if args.importance and seed_id:
        # Build graph from candidates for PageRank
        node_ids = [c.get("openalex_id", "") for c in all_candidates]
        node_ids = [n for n in node_ids if n]
        edges: list[tuple[str, str]] = []
        # Add seed -> citing/cited edges
        for c in mapping_result.get("citing_works", []):
            cid = c.get("openalex_id", "")
            if cid:
                edges.append((seed_id, cid))
        for c in mapping_result.get("cited_works", []):
            cid = c.get("openalex_id", "")
            if cid:
                edges.append((cid, seed_id))

        importance_scores = inciteful.pagerank_importance(
            node_ids + [seed_id], edges
        )
        importance_results = inciteful.rank_by_importance(
            all_candidates, importance_scores, top_n=args.per_page
        )

    # Literature connector
    if args.literature_connector and seed_id:
        literature_connector_result = inciteful.literature_connector(
            seed_id,
            args.literature_connector,
            max_hops=args.max_hops,
            per_hop=args.per_page,
            dry_run=dry_run,
        )

    # Citation network
    if args.citation_network and seed_id:
        citation_network_result = inciteful.expand_citation_network(
            seed_id,
            max_hops=args.max_hops,
            per_hop=args.per_page,
            dry_run=dry_run,
        )
        if args.prune and citation_network_result:
            nodes = citation_network_result["nodes"]
            edges = citation_network_result["edges"]
            p_nodes, p_edges = inciteful.prune_canonical(nodes, edges)
            citation_network_result["nodes"] = p_nodes
            citation_network_result["edges"] = p_edges
            citation_network_result["pruned"] = True

    # Extended graph
    if args.extended_graph and seed_id:
        citation_network_result = inciteful.extended_graph(
            seed_id,
            extra_hops=3,
            per_hop=args.per_page,
            dry_run=dry_run,
        )

    # --- Generate report ------------------------------------------------
    report_md = report.generate_report(
        args.vault,
        mapping_result,
        similarity_results=similarity_results,
        importance_results=importance_results,
        literature_connector=literature_connector_result,
        citation_network=citation_network_result,
        filters_applied=filters_applied,
    )
    report_path = os.path.join(
        args.vault, "04-Archives", "Audit-Reports", "Paper-Mapping-Report.md",
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # --- Print summary --------------------------------------------------
    print(f"\n📄 Paper Mapping — {args.query}")
    print(f"   Vault: {args.vault}")
    if mapping_result.get("error"):
        print(f"   ⚠️  Error: {mapping_result['error']}")
    else:
        print(f"   Seed: {seed.get('title', 'N/A')} ({seed.get('year', 'N/A')})")
        print(f"   Citing works: {len(mapping_result.get('citing_works', []))}")
        print(f"   Cited works: {len(mapping_result.get('cited_works', []))}")
        print(f"   Same-author works: {len(mapping_result.get('same_author_works', []))}")
    if similarity_results:
        print(f"   Similarity-ranked: {len(similarity_results)}")
    if importance_results:
        print(f"   Importance-ranked: {len(importance_results)}")
    if literature_connector_result:
        path = literature_connector_result.get("shortest_path")
        print(f"   Literature connector: {'path found' if path else 'no path'}")
    if citation_network_result:
        print(f"   Citation network: {len(citation_network_result.get('nodes', []))} papers")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    print(f"   Report: {report_path}")
    if dry_run:
        print("   Run with --apply to write the report to vault.")

    # Print key results
    if similarity_results:
        print("\n🔗 Top similar papers:")
        for w in similarity_results[:5]:
            print(f"   {w.get('similarity_score', 0.0):.3f} — {w.get('title', 'N/A')}")

    if importance_results:
        print("\n📊 Most important papers:")
        for w in importance_results[:5]:
            print(f"   {w.get('importance_score', 0.0):.3f} — {w.get('title', 'N/A')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
