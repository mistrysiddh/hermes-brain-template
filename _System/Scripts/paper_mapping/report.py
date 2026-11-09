"""Hermes Brain — Paper Mapping Report Generation.

Generates markdown paper-mapping reports covering seed work, citing
works, cited works, same-author works, Inciteful-inspired features
(similarity ranking, importance ranking, literature connector,
recursive citation network, graph pruning, filters).

Stdlib-only. Multi-harness compliant.
"""

from datetime import datetime
from typing import Any


def generate_report(
    vault: str,
    mapping: dict[str, Any],
    similarity_results: list[dict[str, Any]] | None = None,
    importance_results: list[dict[str, Any]] | None = None,
    literature_connector: dict[str, Any] | None = None,
    citation_network: dict[str, Any] | None = None,
    filters_applied: dict[str, Any] | None = None,
) -> str:
    """Generate markdown paper-mapping report.

    Args:
        vault: Vault path.
        mapping: Core map_paper result.
        similarity_results: Optional similarity-ranked candidates.
        importance_results: Optional PageRank importance-ranked candidates.
        literature_connector: Optional literature connector result.
        citation_network: Optional recursive citation network result.
        filters_applied: Optional dict of filters applied (keyword,
            author, year).

    Returns:
        Markdown report string.

    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Paper Mapping Report",
        f"Generated: {now}",
        f"Vault: {vault}",
        "",
        "## Seed Work",
        "",
    ]

    seed = mapping.get("seed_work") or {}
    if mapping.get("error"):
        lines.append(f"⚠️  Error: {mapping['error']}")
    else:
        lines.append(f"- **Title**: {seed.get('title', 'N/A')}")
        lines.append(f"- **OpenAlex ID**: {seed.get('openalex_id', 'N/A')}")
        lines.append(f"- **DOI**: {seed.get('doi', 'N/A')}")
        lines.append(f"- **Year**: {seed.get('year', 'N/A')}")
        lines.append(f"- **Cited by count**: {seed.get('cited_by_count', 0)}")
        lines.append(f"- **Open access**: {seed.get('is_oa', False)}")
        lines.append(f"- **Authors**: {', '.join(seed.get('authors', []))}")
        lines.append(f"- **URL**: {seed.get('url', 'N/A')}")

    lines += [
        "",
        "## Citing Works (papers that cite the seed)",
        "",
    ]
    citing = mapping.get("citing_works", [])
    if citing:
        lines.append("| Title | Year | Cited by | Authors |")
        lines.append("|-------|------|----------|---------|")
        for w in citing:
            lines.append(
                f"| {w.get('title', 'N/A')} | {w.get('year', 'N/A')} | "
                f"{w.get('cited_by_count', 0)} | {', '.join(w.get('authors', []))} |"
            )
    else:
        lines.append("*None found.*")

    lines += [
        "",
        "## Cited Works (papers cited by the seed)",
        "",
    ]
    cited = mapping.get("cited_works", [])
    if cited:
        lines.append("| Title | Year | Cited by | Authors |")
        lines.append("|-------|------|----------|---------|")
        for w in cited:
            lines.append(
                f"| {w.get('title', 'N/A')} | {w.get('year', 'N/A')} | "
                f"{w.get('cited_by_count', 0)} | {', '.join(w.get('authors', []))} |"
            )
    else:
        lines.append("*None found.*")

    lines += [
        "",
        "## Same-Author Works",
        "",
    ]
    same_author = mapping.get("same_author_works", [])
    if same_author:
        lines.append("| Title | Year | Cited by | Authors |")
        lines.append("|-------|------|----------|---------|")
        for w in same_author:
            lines.append(
                f"| {w.get('title', 'N/A')} | {w.get('year', 'N/A')} | "
                f"{w.get('cited_by_count', 0)} | {', '.join(w.get('authors', []))} |"
            )
    else:
        lines.append("*None found.*")

    # --- Inciteful-inspired sections ---

    if citation_network is not None:
        lines += [
            "",
            "## Recursive Citation Network",
            "",
            f"- Hops explored: {citation_network.get('hops_explored', 'N/A')}",
            f"- Papers discovered: {len(citation_network.get('nodes', []))}",
            f"- Edges: {len(citation_network.get('edges', []))}",
            "",
        ]
        if citation_network.get("nodes"):
            lines.append("### Network Papers")
            lines.append("| Title | Year | Cited by |")
            lines.append("|-------|------|----------|")
            for w in citation_network["nodes"][:20]:
                lines.append(
                    f"| {w.get('title', 'N/A')} | {w.get('year', 'N/A')} | "
                    f"{w.get('cited_by_count', 0)} |"
                )
            if len(citation_network["nodes"]) > 20:
                lines.append(
                    f"| ... and {len(citation_network['nodes']) - 20} more | | |"
                )
            lines.append("")

    if similarity_results is not None:
        lines += [
            "## Similarity Ranking (Inciteful: Link Prediction)",
            "",
            "Papers ranked by similarity to the seed (co-citation + "
            "bibliographic coupling):",
            "",
            "| Title | Similarity | Year | Authors |",
            "|-------|------------|------|---------|",
        ]
        for w in similarity_results[:10]:
            lines.append(
                f"| {w.get('title', 'N/A')} | "
                f"{w.get('similarity_score', 0.0)} | "
                f"{w.get('year', 'N/A')} | {', '.join(w.get('authors', []))} |"
            )
        lines.append("")

    if importance_results is not None:
        lines += [
            "## Importance Ranking (Inciteful: PageRank)",
            "",
            "Papers ranked by structural centrality in the citation graph:",
            "",
            "| Title | Importance | Year | Cited by |",
            "|-------|------------|------|----------|",
        ]
        for w in importance_results[:10]:
            lines.append(
                f"| {w.get('title', 'N/A')} | "
                f"{w.get('importance_score', 0.0)} | "
                f"{w.get('year', 'N/A')} | {w.get('cited_by_count', 0)} |"
            )
        lines.append("")

    if literature_connector is not None:
        lines += [
            "## Literature Connector (Two-Paper Connection)",
            "",
            f"- Paper A: {literature_connector.get('paper_a', 'N/A')}",
            f"- Paper B: {literature_connector.get('paper_b', 'N/A')}",
            f"- Max hops: {literature_connector.get('max_hops', 'N/A')}",
            f"- Shortest path found: {'Yes' if literature_connector.get('shortest_path') else 'No'}",
            "",
        ]
        if literature_connector.get("shortest_path"):
            path = literature_connector["shortest_path"]
            lines.append(f"### Shortest Path ({len(path)} hops)")
            lines.append(" → ".join(path))
            lines.append("")

    if filters_applied is not None:
        lines += [
            "## Filters Applied",
            "",
        ]
        for key, value in filters_applied.items():
            if value:
                lines.append(f"- {key}: {value}")
        lines.append("")

    lines += [
        "",
        "## Summary",
        f"- Citing works: {len(citing)}",
        f"- Cited works: {len(cited)}",
        f"- Same-author works: {len(same_author)}",
        "",
    ]

    if citation_network:
        lines.append(
            f"- Citation network papers: {len(citation_network.get('nodes', []))}"
        )
        lines.append(
            f"- Citation network edges: {len(citation_network.get('edges', []))}"
        )
    if similarity_results:
        lines.append(f"- Similarity-ranked candidates: {len(similarity_results)}")
    if importance_results:
        lines.append(f"- Importance-ranked candidates: {len(importance_results)}")
    if literature_connector:
        lines.append(
            f"- Literature connector path: "
            f"{'found' if literature_connector.get('shortest_path') else 'not found'}"
        )

    lines += [
        "",
        "## Next Steps",
        "",
        "- Review citing works for recent developments on this topic",
        "- Check cited works for foundational references",
        "- Explore same-author works for related research",
        "- Use similarity ranking to find closely related papers",
        "- Use importance ranking to find foundational/canonical works",
        "- Use literature connector to trace citation paths between two papers",
        "- Use graph pruning to dampen canonical paper dominance",
        "",
    ]

    return "\n".join(lines)
