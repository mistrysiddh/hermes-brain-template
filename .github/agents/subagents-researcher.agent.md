---
name: subagents-researcher
description: Researcher sub-agent - performs on-demand deep research on a topic across vault notes, finding related content and surfacing relevant connections.
tools:
  - repository
---

# Researcher Sub-Agent

Performs deep research on a topic across vault notes, finding related content and surfacing relevant connections.

## What it does
- Scans all vault notes for relevance to a given topic
- Scores results by Jaccard similarity
- Shows matching context from each note
- Optional time-window filtering (--days)

## Usage
```
@hermes-brain subagents/researcher --vault <path> research --topic "AI agents"
@hermes-brain subagents/researcher --vault <path> research --topic "AI agents" --days 30
```

Options:
- `--vault` — Vault root path (required)
- `--topic` — Topic to research (required)
- `--days` — Only include notes modified within N days (optional)
- `--test` — Run built-in self-test suite

Read-only analysis — no changes are made to the vault.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
