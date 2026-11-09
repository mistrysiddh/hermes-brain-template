"""Hermes Brain — Paper Mapping HTTP Client.

Stdlib urllib-based HTTP helpers for the OpenAlex API.
No external dependencies.

Multi-harness compliant: stdlib-only, dry-run aware.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

OPENALEX_BASE = "https://api.openalex.org"


def http_get(url: str, timeout: int = 15) -> dict[str, Any]:
    """GET a URL and return parsed JSON.

    Raises urllib.error.HTTPError or urllib.error.URLError on failure.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Hermes-Brain-PaperMapping/1.0 "
                "(mailto:hermes@brain.template)"
            ),
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_url(base: str, params: dict[str, str]) -> str:
    """Build a URL with query parameters."""
    return f"{base}?{urllib.parse.urlencode(params)}"


def quote_doi(doi: str) -> str:
    """URL-encode a DOI for use in an API path."""
    return urllib.parse.quote(doi, safe="")


def extract_short_id(openalex_id: str) -> str:
    """Extract the short W-id from a full OpenAlex URL or return as-is."""
    if openalex_id.startswith("http"):
        return openalex_id.split("/")[-1]
    return openalex_id
