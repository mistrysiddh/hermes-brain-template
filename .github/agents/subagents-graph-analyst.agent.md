---
name: subagents-graph-analyst
description: Graph Analyst sub-agent - monthly navigation analysis: MOC health, centrality, dead ends.
tools:
  - repository
---

# Graph Analyst Sub-Agent

Performs monthly navigation analysis on the vault knowledge graph.

## What it does
- Counts total notes and links
- Identifies most linked notes (centrality)
- Identifies dead ends (notes with no outgoing links)
- Identifies top MOCs (most outgoing links)
- Groups link connections by directory

## Usage
```
@hermes-brain subagents/graph-analyst --vault <path> scan
```

Options:
- `--vault` — Vault root path (required)
- `--test` — Run built-in self-test suite

Read-only analysis — no changes are made to the vault.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
