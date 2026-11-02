---
name: subagents-curator
description: Curator sub-agent - quarterly prune/archive review — identifies stale notes, stubs, and archive candidates.
tools:
  - repository
---

# Curator Sub-Agent

Performs quarterly curation — identifies stale notes, stubs, and archive candidates.

## What it does
- Scans all vault notes for staleness (not modified in 180+ days)
- Identifies stub notes (less than 50 characters of content)
- Reports candidates for review/archive

## Usage
```
@hermes-brain subagents/curator --vault <path> scan
@hermes-brain subagents/curator --vault <path> scan --apply
```

Options:
- `--vault` — Vault root path (required)
- `--apply` — Flag for review (overrides --dry-run default)
- `--test` — Run built-in self-test suite

Read-only analysis in dry-run mode — no changes are made to the vault unless --apply is used.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
