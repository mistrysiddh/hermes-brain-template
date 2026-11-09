"""Hermes Brain — Borg Skill-Pack Digestion (multi-harness compatible).

Converts heterogeneous agent skill-packs into a secure, typed,
de-duplicated, searchable and tested catalog of Roles, Skills, tools,
resources, workflows and skids — atomic, reusable primitives.

Based on skill-pack-digest.txt v25.0 — a self-contained operating reference.

Sub-modules:
- layout: Repo layout (§19.1) — directories, registry files
- models: Record schema ⟨M,R,C,P,T,N,X,E,D⟩ + 7 kinds
- trust_scanner: TRUST checks (§5.4) — license, secrets, injection, etc.
- art_adapters: ART absorption adapters (§5.1) — hooks, commands, scripts, etc.
- cli: CLI entry point

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only
  - --test built-in self-test suite
"""

__all__ = [
    "layout",
    "models",
    "trust_scanner",
    "art_adapters",
    "cli",
]
