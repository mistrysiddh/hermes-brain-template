"""Hermes Brain — Borg Pipeline Sub-package.

Pipeline agents S1–S10 (§4.1):
- S1 Ingestor — Unpack, type, provenance, trust-scan
- S2 Profiler — One rubric per record
- S3 Directory — Roles × Skills ontology
- S4 Skids — Find L0 primitives
- S5 Decompose — Composites → DAGs
- S6 Tacit — Judgment and nuance
- S7 Dedup — Canonicalize + diversity
- S8 Measure — Empirical tests
- S9 Search — Retrieval + routing
- S10 Govern — Record why; loops

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

__all__ = [
    "s1_ingestor",
]
