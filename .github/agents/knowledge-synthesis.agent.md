---
name: knowledge-synthesis
description: BASB/ZK-inspired knowledge consolidation — extracts atomic ideas from session notes, performs progressive summarization (raw → key takeaways → durable facts), builds Map of Content (MOC) notes for recurring topics, and injects bidirectional wikilinks between sessions and MOCs.
tools:
  - repository
---

# Knowledge Synthesis Agent

Consolidates session archives into durable, linked knowledge following BASB/Zettelkasten principles.

## What it does

1. **Extracts atomic ideas** from session notes (one idea per candidate note)
2. **Progressive summarization** — distills long sessions into layered summaries (summary → key takeaways → actionable facts)
3. **Builds MOCs** (Maps of Content / structure notes) for topics recurring across sessions
4. **Auto-inserts bidirectional wikilinks** between related notes
5. **Produces a synthesis report** of what was linked, summarized, and structured

## Subcommands

| Subcommand | What it does |
|------------|--------------|
| `vault` | Scan vault sessions within a time window |
| `scripts` | Script hygiene check (module-level paths, hardcoded paths, missing `--vault`) |
| `sessions` | Session residue check (stale cron files, orphaned canvases) |
| `security` | Secret exposure detection |
| `all` | Run every category |

## Usage

```
@hermes-brain knowledge-synthesis --vault <path> --days 14 --moc --atomic --link
```

Options:
- `--days N` — Number of days to scan (default: 14)
- `--moc` — Build Map of Content notes for recurring topics
- `--atomic` — Extract atomic ideas as candidate notes in Memory-Review
- `--link` — Inject bidirectional wikilinks between sessions and MOCs

Produces a `Knowledge-Synthesis-YYYY-MM-DD.md` report in `04-Archives/Audit-Reports/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
