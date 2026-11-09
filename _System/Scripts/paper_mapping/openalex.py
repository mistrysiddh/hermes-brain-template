"""Hermes Brain — Paper Mapping OpenAlex API Wrapper.

OpenAlex API functions:
- Search works by title/query
- Fetch work by DOI
- Fetch work by OpenAlex ID
- Works that cite a given work (citing works)
- Works cited by a given work (cited works / referenced works)
- Works by the same author
- Author details

All functions return raw OpenAlex JSON responses.
Stdlib-only (uses http_client).

Multi-harness compliant: stdlib-only, dry-run aware.
"""

from typing import Any

from . import http_client


def search(query: str, per_page: int = 10) -> dict[str, Any]:
    """Search OpenAlex works by title/query."""
    params = {"search": query, "per-page": str(per_page)}
    return http_client.http_get(
        http_client.build_url(http_client.OPENALEX_BASE + "/works", params)
    )


def work_by_doi(doi: str) -> dict[str, Any]:
    """Fetch a work by DOI."""
    doi_encoded = http_client.quote_doi(doi)
    return http_client.http_get(
        f"{http_client.OPENALEX_BASE}/works/doi:{doi_encoded}"
    )


def work(openalex_id: str) -> dict[str, Any]:
    """Fetch a work by OpenAlex ID (W-number or full URL)."""
    short_id = http_client.extract_short_id(openalex_id)
    return http_client.http_get(
        f"{http_client.OPENALEX_BASE}/works/{short_id}"
    )


def citing_works(openalex_id: str, per_page: int = 10) -> dict[str, Any]:
    """Works that cite this work (papers that reference it)."""
    params = {"filter": f"cites:{openalex_id}", "per-page": str(per_page)}
    return http_client.http_get(
        http_client.build_url(http_client.OPENALEX_BASE + "/works", params)
    )


def cited_works(openalex_id: str, per_page: int = 10) -> dict[str, Any]:
    """Works cited by this work (papers it references).

    OpenAlex has no direct inverse filter, so we fetch the work itself,
    read its referenced_works array, then look up each referenced work.
    """
    try:
        work_data = work(openalex_id)
        ref_ids = work_data.get("referenced_works", [])[:per_page]
        results = []
        for ref_id in ref_ids:
            try:
                ref_work = work(ref_id)
                results.append(ref_work)
            except Exception:
                continue
        return {"results": results, "count": len(results)}
    except Exception:
        return {"results": [], "count": 0}


def author_works(author_id: str, per_page: int = 10) -> dict[str, Any]:
    """Works by the same author."""
    params = {
        "filter": f"authorships.author.id:{author_id}",
        "per-page": str(per_page),
    }
    return http_client.http_get(
        http_client.build_url(http_client.OPENALEX_BASE + "/works", params)
    )


def author(openalex_author_id: str) -> dict[str, Any]:
    """Fetch author details by OpenAlex author ID."""
    short_id = http_client.extract_short_id(openalex_author_id)
    return http_client.http_get(
        f"{http_client.OPENALEX_BASE}/authors/{short_id}"
    )
