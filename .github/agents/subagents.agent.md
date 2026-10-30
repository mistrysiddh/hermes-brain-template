---
name: subagents
description: Multi-agent vault maintenance — six sub-agents (ingestor, linker, reviewer, researcher, graph-analyst, curator) with dry-run default and human-in-the-loop approval.
tools:
  - repository
---

# Subagents Agent

Six sub-agents for vault maintenance, each with a specific role:

| Agent | Role | Trigger |
|-------|------|---------|
| ingestor | Writes new material from `raw/` into the vault | On new files in `raw/` |
| linker | Finds and adds missing connections between notes | Weekly / on demand |
| reviewer | Read-only vault audit — broken links, orphans, drift | Weekly |
| researcher | On-demand deep research on a topic across the vault | On demand |
| graph-analyst | Monthly navigation analysis — MOC health, clusters | Monthly |
| curator | Quarterly prune/archive review — stale notes, duplicates | Quarterly |

## Usage

```
@hermes-brain subagents --vault <path> ingestor
@hermes-brain subagents --vault <path> linker --threshold 0.6
@hermes-brain subagents --vault <path> reviewer
@hermes-brain subagents --vault <path> researcher --topic "AI agents"
@hermes-brain subagents --vault <path> graph-analyst
@hermes-brain subagents --vault <path> curator
```

Options:
- `--vault` — Vault root path (required)
- `--apply` — Apply changes (overrides `--dry-run` default) — for ingestor, linker, curator
- `--threshold` — Linker similarity threshold 0-1 (default: 0.6)
- `--topic` — Researcher topic (required for researcher)
- `--days` — Researcher time window in days (optional)
- `--save` — Save report to vault
- `--dry-run` — Preview only (default)

## Safety

- All agents run in `--dry-run` by default — nothing is auto-written
- `--apply` writes changes to the vault only when explicitly requested
- Reports are saved to `04-Archives/Agents/reports/`

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
