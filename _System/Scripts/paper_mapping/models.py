"""Hermes Brain — Paper Mapping Data Models.

WorkSummary type, ID extraction, and work summarization helpers.

Stdlib-only. Multi-harness compliant.
"""

from typing import Any


def extract_openalex_id(work: dict[str, Any]) -> str:
    """Extract the short OpenAlex W-id from a work dict."""
    wid = work.get("id", "")
    if wid.startswith("https://openalex.org/"):
        wid = wid.split("/")[-1]
    return wid


def summarize_work(work: dict[str, Any]) -> dict[str, Any]:
    """Produce a compact summary dict for a work.

    Returns:
        {
            "openalex_id": str,
            "title": str,
            "year": int | None,
            "doi": str | None,
            "cited_by_count": int,
            "is_oa": bool,
            "authors": list[str],     # up to 3
            "url": str,
        }

    """
    return {
        "openalex_id": extract_openalex_id(work),
        "title": work.get("display_name", work.get("title", "")),
        "year": work.get("publication_year"),
        "doi": work.get("doi"),
        "cited_by_count": work.get("cited_by_count", 0),
        "is_oa": work.get("open_access", {}).get("is_oa", False),
        "authors": [
            a.get("author", {}).get("display_name", "Unknown")
            for a in work.get("authorships", [])
        ][:3],
        "url": work.get("ids", {}).get("openalex", ""),
    }
