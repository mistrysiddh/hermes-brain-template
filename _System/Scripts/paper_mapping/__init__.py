"""Hermes Brain — Paper Mapping (multi-harness compatible).

Paper discovery and citation-network mapping via OpenAlex API, with
Inciteful.XYZ-inspired algorithms (similarity ranking, importance
ranking, literature connector, graph pruning, keyword/author/time
filters, recursive citation expansion).

Sub-modules:
- http_client: stdlib urllib HTTP helpers
- openalex: OpenAlex API wrapper
- inciteful: Inciteful-inspired algorithms on OpenAlex data
- models: WorkSummary type, extract/summarize helpers
- mapping: Core paper mapping logic
- report: Report generation
- cli: CLI entry point

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only (urllib for HTTP)
  - --test built-in self-test suite
"""

__all__ = [
    "http_client",
    "openalex",
    "inciteful",
    "models",
    "mapping",
    "report",
    "cli",
]
