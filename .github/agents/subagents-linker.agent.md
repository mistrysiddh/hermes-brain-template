---
name: subagents-linker
description: Linker sub-agent - finds missing links between related vault notes using Jaccard similarity scoring.
tools:
  - repository
---

# Linker Sub-Agent

Finds notes that share topics but aren't linked, and suggests or adds wikilinks between them.

## What it does
- Scans all vault notes and computes Jaccard similarity between each pair
- Identifies pairs of notes with similar content that aren't already linked
- Suggests or adds bidirectional wikilinks between related notes

## Usage
```
@hermes-brain subagents/linker --vault <path> scan --threshold 0.6
@hermes-brain subagents/linker --vault <path> scan --apply
```

Options:
- `--vault` — Vault root path (required)
- `--threshold` — Similarity threshold 0-1 (default: 0.6)
- `--apply` — Apply links (overrides --dry-run default)
- `--test` — Run built-in self-test suite

Writes links to source notes when `--apply` is used.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
