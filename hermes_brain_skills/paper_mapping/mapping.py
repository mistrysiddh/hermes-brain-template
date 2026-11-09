"""Hermes Brain — Paper Mapping Core Logic.

map_paper: find a seed paper via OpenAlex, then gather citing works,
cited works, and same-author papers.

Stdlib-only. Multi-harness compliant.
"""

from typing import Any

from . import openalex
from .models import summarize_work, extract_openalex_id


def map_paper(
    seed_query: str,
    per_page: int = 10,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Map a paper: find it via OpenAlex, then gather citing works,
    cited works, and same-author papers.

    Returns:
        {
            "seed_query": str,
            "seed_work": WorkSummary | None,
            "citing_works": list[WorkSummary],
            "cited_works": list[WorkSummary],
            "same_author_works": list[WorkSummary],
            "dry_run": bool,
            "error": str | None,
        }

    """
    result: dict[str, Any] = {
        "seed_query": seed_query,
        "seed_work": None,
        "citing_works": [],
        "cited_works": [],
        "same_author_works": [],
        "dry_run": dry_run,
        "error": None,
    }

    try:
        # Step 1: Search for the seed work
        search_resp = openalex.search(seed_query, per_page=1)
        results = search_resp.get("results", [])
        if not results:
            result["error"] = f"No work found matching: {seed_query}"
            return result

        seed = results[0]
        result["seed_work"] = summarize_work(seed)
        seed_id = extract_openalex_id(seed)
        seed_authors = seed.get("authorships", [])

        # Step 2: Citing works (papers that cite the seed)
        citing_resp = openalex.citing_works(seed_id, per_page=per_page)
        result["citing_works"] = [
            summarize_work(w) for w in citing_resp.get("results", [])
        ]

        # Step 3: Cited works (papers the seed references)
        cited_resp = openalex.cited_works(seed_id, per_page=per_page)
        result["cited_works"] = [
            summarize_work(w) for w in cited_resp.get("results", [])
        ]

        # Step 4: Same-author works
        author_ids = [
            a.get("author", {}).get("id", "")
            for a in seed_authors
            if a.get("author", {}).get("id")
        ]
        if author_ids:
            author_resp = openalex.author_works(author_ids[0], per_page=per_page)
            result["same_author_works"] = [
                summarize_work(w)
                for w in author_resp.get("results", [])
                if extract_openalex_id(w) != seed_id
            ][:per_page]

    except Exception as e:
        result["error"] = str(e)

    return result
