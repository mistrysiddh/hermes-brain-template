---
name: subagents-reviewer
description: Reviewer sub-agent - read-only vault audit checking for broken wikilinks, orphaned notes, and link density.
tools:
  - repository
---

# Reviewer Sub-Agent

Performs read-only vault audit to check link health and content organization.

## What it does
- Counts total notes, wikilinks, broken links, and orphaned notes
- Identifies broken wikilinks (links to non-existent targets)
- Identifies orphaned notes (notes with no incoming links from any other note)
- Groups notes by top-level directory

## Usage
```
@hermes-brain subagents/reviewer --vault <path> scan
```

Options:
- `--vault` — Vault root path (required)
- `--test` — Run built-in self-test suite

Read-only audit — no changes are made to the vault.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
