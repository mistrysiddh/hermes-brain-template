"""Hermes Brain — Inciteful.XYZ-inspired Algorithms.

Implements Inciteful.XYZ features on top of OpenAlex data:

1. **Recursive citation network expansion** — expand beyond 1-hop
   citing/cited works to build a multi-hop citation graph.
2. **Similarity ranking** — link prediction based on co-citation +
   bibliographic coupling between papers.
3. **Importance ranking** — PageRank-style structural centrality in
   the citation graph.
4. **Literature Connector** — two-paper connection via bidirectional
   search up to 6 hops, finding shortest citation paths.
5. **Graph pruning** — dampen impact of canonical papers cited by
   everyone (prevents gravity wells).
6. **Keyword/author/time filters** — filter results by keywords in
   titles, authors, or publication year range.
7. **Extended graph** — optional multi-hop expansion beyond direct
   citations.

Note: Inciteful.XYZ is a web platform (incitefulmed.com/academic/)
without a public API. These algorithms operate on OpenAlex data
(240M+ works, 2B+ citations indexed) to reproduce Inciteful's
feature set using free, open data.

Stdlib-only. Multi-harness compliant.
"""

from collections import deque, defaultdict
from typing import Any

from . import openalex
from .models import summarize_work


# ---------------------------------------------------------------------------
# Recursive citation network expansion
# ---------------------------------------------------------------------------

def expand_citation_network(
    seed_id: str,
    max_hops: int = 2,
    per_hop: int = 10,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Recursively expand a citation network from a seed paper.

    Builds a graph of papers citing and cited by the seed, expanding
    outward up to max_hops levels. Each paper's citing and cited works
    are fetched and added as nodes/edges.

    Returns:
        {
            "nodes": list[WorkSummary],      # all papers discovered
            "edges": list[tuple[str, str]],  # (cited_id, citing_id)
            "hops_explored": int,
            "dry_run": bool,
        }

    Args:
        seed_id: OpenAlex ID of the seed paper.
        max_hops: Maximum recursion depth (Inciteful uses up to 6).
        per_hop: Max results per hop.
        dry_run: If True, no side effects (network calls still occur
            to fetch data, but results are not persisted).

    """
    seed_id = _normalize_id(seed_id)
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[tuple[str, str]] = []
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(seed_id, 0)])

    while queue:
        current_id, hop = queue.popleft()
        if current_id in visited or hop > max_hops:
            continue
        visited.add(current_id)

        try:
            work_data = openalex.work(current_id)
        except Exception:
            continue

        summary = summarize_work(work_data)
        nodes[current_id] = summary

        # Citing works (papers that cite current)
        try:
            citing = openalex.citing_works(current_id, per_page=per_hop)
            for w in citing.get("results", []):
                wid = _normalize_id(w.get("id", ""))
                if wid and wid not in nodes:
                    nodes[wid] = summarize_work(w)
                if wid:
                    edges.append((current_id, wid))  # current cited by wid
                    if hop + 1 <= max_hops and wid not in visited:
                        queue.append((wid, hop + 1))
        except Exception:
            pass

        # Cited works (papers cited by current)
        try:
            cited = openalex.cited_works(current_id, per_page=per_hop)
            for w in cited.get("results", []):
                wid = _normalize_id(w.get("id", ""))
                if wid and wid not in nodes:
                    nodes[wid] = summarize_work(w)
                if wid:
                    edges.append((wid, current_id))  # wid cited by current
                    if hop + 1 <= max_hops and wid not in visited:
                        queue.append((wid, hop + 1))
        except Exception:
            pass

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "hops_explored": max_hops,
        "dry_run": dry_run,
    }


def _normalize_id(openalex_id: str) -> str:
    """Normalize an OpenAlex ID to short W-id form."""
    return openalex_id.split("/")[-1] if openalex_id.startswith("http") else openalex_id


# ---------------------------------------------------------------------------
# Similarity ranking (co-citation + bibliographic coupling)
# ---------------------------------------------------------------------------

def similarity_score(
    paper_a_id: str,
    paper_b_id: str,
    citing_index: dict[str, set[str]] | None = None,
    cited_index: dict[str, set[str]] | None = None,
) -> float:
    """Compute similarity between two papers using link prediction.

    Combines:
    - Co-citation: how many papers cite both A and B
    - Bibliographic coupling: how many papers both A and B cite

    Returns a score between 0.0 and 1.0.

    Args:
        paper_a_id: OpenAlex ID of paper A.
        paper_b_id: OpenAlex ID of paper B.
        citing_index: Optional precomputed map paper_id -> set of citing IDs.
        cited_index: Optional precomputed map paper_id -> set of cited IDs.

    """
    paper_a_id = _normalize_id(paper_a_id)
    paper_b_id = _normalize_id(paper_b_id)

    if citing_index is None:
        citing_index = {}
    if cited_index is None:
        cited_index = {}

    citing_a = citing_index.get(paper_a_id, set())
    citing_b = citing_index.get(paper_b_id, set())
    cited_a = cited_index.get(paper_a_id, set())
    cited_b = cited_index.get(paper_b_id, set())

    # Co-citation overlap (Jaccard)
    citing_union = citing_a | citing_b
    citing_overlap = citing_a & citing_b
    co_citation = (
        len(citing_overlap) / len(citing_union) if citing_union else 0.0
    )

    # Bibliographic coupling overlap (Jaccard)
    cited_union = cited_a | cited_b
    cited_overlap = cited_a & cited_b
    bib_coupling = (
        len(cited_overlap) / len(cited_union) if cited_union else 0.0
    )

    # Combined similarity: average of the two
    return round((co_citation + bib_coupling) / 2.0, 4)


def rank_by_similarity(
    candidates: list[dict[str, Any]],
    reference_id: str,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Rank candidate papers by similarity to a reference paper.

    Adds a 'similarity_score' field to each candidate and sorts
    descending.

    Args:
        candidates: List of WorkSummary dicts (must have 'openalex_id').
        reference_id: OpenAlex ID of the reference paper.
        top_n: Max number of results to return.

    Returns:
        List of candidates with similarity_score, sorted descending.

    """
    reference_id = _normalize_id(reference_id)
    scored = []
    for c in candidates:
        cid = c.get("openalex_id", "")
        score = similarity_score(reference_id, cid)
        c_with_score = dict(c)
        c_with_score["similarity_score"] = score
        scored.append(c_with_score)

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Importance ranking (PageRank-style structural centrality)
# ---------------------------------------------------------------------------

def pagerank_importance(
    nodes: list[str],
    edges: list[tuple[str, str]],
    damping: float = 0.85,
    iterations: int = 20,
) -> dict[str, float]:
    """Compute PageRank-style importance scores for papers in a graph.

    Args:
        nodes: List of paper IDs.
        edges: List of (cited_id, citing_id) tuples — edge means
            cited_id is cited by citing_id.
        damping: PageRank damping factor (default 0.85).
        iterations: Number of PageRank iterations.

    Returns:
        Dict mapping paper_id -> importance score (0.0–1.0).

    """
    if not nodes:
        return {}

    # Build adjacency: for each node, who does it cite (outgoing edges)
    out_edges: dict[str, list[str]] = defaultdict(list)
    for cited_id, citing_id in edges:
        out_edges[citing_id].append(cited_id)

    # Initialize PageRank
    pr: dict[str, float] = {n: 1.0 / len(nodes) for n in nodes}

    for _ in range(iterations):
        new_pr: dict[str, float] = {n: (1.0 - damping) / len(nodes) for n in nodes}
        for n in nodes:
            for target in out_edges.get(n, []):
                if target in new_pr:
                    out_count = len(out_edges[n]) or 1
                    new_pr[target] += damping * pr[n] / out_count
        pr = new_pr

    # Normalize to 0–1
    max_score = max(pr.values()) if pr else 1.0
    if max_score > 0:
        pr = {k: round(v / max_score, 4) for k, v in pr.items()}

    return pr


def rank_by_importance(
    candidates: list[dict[str, Any]],
    importance_scores: dict[str, float],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Rank candidates by PageRank importance score.

    Adds 'importance_score' field and sorts descending.

    Args:
        candidates: List of WorkSummary dicts.
        importance_scores: Dict from pagerank_importance.
        top_n: Max results.

    Returns:
        Sorted list with importance_score added.

    """
    scored = []
    for c in candidates:
        cid = c.get("openalex_id", "")
        c_with_score = dict(c)
        c_with_score["importance_score"] = importance_scores.get(cid, 0.0)
        scored.append(c_with_score)

    scored.sort(key=lambda x: x["importance_score"], reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Literature Connector — two-paper connection
# ---------------------------------------------------------------------------

def literature_connector(
    paper_a_id: str,
    paper_b_id: str,
    max_hops: int = 6,
    per_hop: int = 10,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Find citation paths between two papers (Inciteful Literature Connector).

    Runs bidirectional BFS from both papers simultaneously, meeting
    in the middle. Searches up to max_hops deep from each side.

    Returns:
        {
            "paper_a": str,
            "paper_b": str,
            "paths": list[list[str]],  # each path is a list of paper IDs
            "shortest_path": list[str] | None,
            "max_hops": int,
            "dry_run": bool,
        }

    Args:
        paper_a_id: OpenAlex ID of first paper.
        paper_b_id: OpenAlex ID of second paper.
        max_hops: Max search depth from each side (Inciteful: up to 6).
        per_hop: Max results per hop.
        dry_run: If True, no persistence side effects.

    """
    paper_a_id = _normalize_id(paper_a_id)
    paper_b_id = _normalize_id(paper_b_id)

    if paper_a_id == paper_b_id:
        return {
            "paper_a": paper_a_id,
            "paper_b": paper_b_id,
            "paths": [[paper_a_id]],
            "shortest_path": [paper_a_id],
            "max_hops": max_hops,
            "dry_run": dry_run,
        }

    # Bidirectional BFS
    forward_visited: dict[str, str | None] = {paper_a_id: None}
    backward_visited: dict[str, str | None] = {paper_b_id: None}
    forward_queue: deque[str] = deque([paper_a_id])
    backward_queue: deque[str] = deque([paper_b_id])
    meeting_node: str | None = None

    def get_neighbors(pid: str) -> list[str]:
        """Get all directly connected paper IDs (citing + cited)."""
        neighbors: list[str] = []
        try:
            citing = openalex.citing_works(pid, per_page=per_hop)
            for w in citing.get("results", []):
                wid = _normalize_id(w.get("id", ""))
                if wid:
                    neighbors.append(wid)
        except Exception:
            pass
        try:
            cited = openalex.cited_works(pid, per_page=per_hop)
            for w in cited.get("results", []):
                wid = _normalize_id(w.get("id", ""))
                if wid:
                    neighbors.append(wid)
        except Exception:
            pass
        return neighbors

    depth = 0
    while forward_queue and backward_queue and depth < max_hops:
        # Expand forward side
        for _ in range(len(forward_queue)):
            current = forward_queue.popleft()
            if current in backward_visited:
                meeting_node = current
                break
            for neighbor in get_neighbors(current):
                if neighbor not in forward_visited:
                    forward_visited[neighbor] = current
                    forward_queue.append(neighbor)
        if meeting_node:
            break

        # Expand backward side
        for _ in range(len(backward_queue)):
            current = backward_queue.popleft()
            if current in forward_visited:
                meeting_node = current
                break
            for neighbor in get_neighbors(current):
                if neighbor not in backward_visited:
                    backward_visited[neighbor] = current
                    backward_queue.append(neighbor)
        if meeting_node:
            break

        depth += 1

    # Reconstruct paths
    paths: list[list[str]] = []
    shortest_path: list[str] | None = None

    if meeting_node:
        # Build path from A to meeting node
        path_a: list[str] = []
        node: str | None = meeting_node
        while node is not None:
            path_a.append(node)
            node = forward_visited[node]
        path_a.reverse()  # A -> meeting_node

        # Build path from meeting node to B
        path_b: list[str] = []
        node = backward_visited[meeting_node]
        while node is not None:
            path_b.append(node)
            node = backward_visited[node]

        full_path = path_a + path_b
        paths = [full_path]
        shortest_path = full_path

    return {
        "paper_a": paper_a_id,
        "paper_b": paper_b_id,
        "paths": paths,
        "shortest_path": shortest_path,
        "max_hops": max_hops,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Graph pruning — dampen canonical papers
# ---------------------------------------------------------------------------

def prune_canonical(
    nodes: list[dict[str, Any]],
    edges: list[tuple[str, str]],
    threshold: float = 0.3,
) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    """Prune highly-cited canonical papers that create "gravity wells."

    Inciteful dampens the impact of papers cited by everyone so they
    don't dominate discovery results. This function removes edges to
    nodes whose citation frequency exceeds the threshold.

    Args:
        nodes: List of WorkSummary dicts (with 'cited_by_count').
        edges: List of (cited_id, citing_id) tuples.
        threshold: Fraction of nodes above which a paper is considered
            canonical (default 0.3 = top 30% by citation count).

    Returns:
        (pruned_nodes, pruned_edges)

    """
    if not nodes:
        return nodes, edges

    # Count how many times each node is cited (incoming edges)
    citation_freq: dict[str, int] = defaultdict(int)
    for cited_id, _citing_id in edges:
        citation_freq[cited_id] += 1

    max_freq = max(citation_freq.values()) if citation_freq else 1
    cutoff = max_freq * threshold

    canonical_ids = {
        nid for nid, freq in citation_freq.items() if freq > cutoff
    }

    # Also consider OpenAlex cited_by_count as secondary signal
    for n in nodes:
        if n.get("cited_by_count", 0) > cutoff * 100:  # rough scale
            canonical_ids.add(n["openalex_id"])

    # Filter edges: remove edges pointing TO canonical nodes
    pruned_edges = [
        (cited, citing)
        for cited, citing in edges
        if cited not in canonical_ids
    ]

    # Keep all nodes (don't remove papers, just dampen their edges)
    pruned_nodes = list(nodes)

    return pruned_nodes, pruned_edges


# ---------------------------------------------------------------------------
# Filters — keyword, author, time
# ---------------------------------------------------------------------------

def filter_by_keyword(
    candidates: list[dict[str, Any]],
    keywords: list[str],
) -> list[dict[str, Any]]:
    """Filter papers by keywords in title (case-insensitive, any match)."""
    if not keywords:
        return candidates
    kw_lower = [k.lower() for k in keywords]
    return [
        c for c in candidates
        if any(kw in (c.get("title", "") or "").lower() for kw in kw_lower)
    ]


def filter_by_author(
    candidates: list[dict[str, Any]],
    authors: list[str],
) -> list[dict[str, Any]]:
    """Filter papers by author name (case-insensitive, any match)."""
    if not authors:
        return candidates
    auth_lower = [a.lower() for a in authors]
    return [
        c for c in candidates
        if any(
            au.lower() in (", ".join(c.get("authors", [])) or "").lower()
            for au in auth_lower
        )
    ]


def filter_by_year(
    candidates: list[dict[str, Any]],
    min_year: int | None = None,
    max_year: int | None = None,
) -> list[dict[str, Any]]:
    """Filter papers by publication year range."""
    result = []
    for c in candidates:
        year = c.get("year")
        if year is None:
            continue
        if min_year is not None and year < min_year:
            continue
        if max_year is not None and year > max_year:
            continue
        result.append(c)
    return result


# ---------------------------------------------------------------------------
# Extended graph — multi-hop expansion beyond direct citations
# ---------------------------------------------------------------------------

def extended_graph(
    seed_id: str,
    extra_hops: int = 3,
    per_hop: int = 10,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Extend a citation graph by extra hops beyond base 2-hop paths.

    Inciteful can extend paths by extra 3 hops beyond base 2-hop
    literature connector paths.

    Args:
        seed_id: OpenAlex ID of the seed paper.
        extra_hops: Additional hops beyond the base (default 3).
        per_hop: Max results per hop.
        dry_run: If True, no persistence side effects.

    Returns:
        Same shape as expand_citation_network.

    """
    return expand_citation_network(
        seed_id,
        max_hops=2 + extra_hops,
        per_hop=per_hop,
        dry_run=dry_run,
    )
