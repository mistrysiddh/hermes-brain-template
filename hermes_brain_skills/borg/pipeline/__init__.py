"""Borg pipeline agents — S1–S10.

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

__version__ = "1.0.0"

__all__ = ["s1_ingestor", "s2_profiler", "s3_directory", "s4_skids", "s5_decompose", "s6_tacit", "s7_dedup", "s8_measure", "s9_search", "prompts"]
