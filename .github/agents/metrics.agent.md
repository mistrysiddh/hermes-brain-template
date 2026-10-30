---
name: metrics
description: Dated metrics snapshot command — computes vault-wide metrics (notes, links, sessions, tags, MOCs, stale content) and writes a dated snapshot markdown file for trend tracking over time.
tools:
  - repository
---

# Metrics Agent

Computes vault-wide metrics and produces dated snapshots for trend tracking.

## What it does

| Category | What it measures |
|----------|-----------------|
| notes | Total note count, notes per directory, recent activity |
| links | Total wikilinks, unique targets, broken links, link density |
| sessions | Session count, date range, sessions per month |
| tags | Unique tag count, top tag frequency distribution |
| mocs | MOC health, orphaned MOCs (no wikilinks) |
| stale | Notes not modified in N days |

## Usage

```
@hermes-brain metrics --vault <path> snapshot --days 30
@hermes-brain metrics --vault <path> snapshot --categories notes,links --days 30 --apply
@hermes-brain metrics --vault <path> snapshot --digest-type weekly --days 30 --apply
```

Options:
- `--vault` — Vault root path (required)
- `--days N` — Activity window in days (default: 30)
- `--stale-days N` — Stale threshold in days (default: 90)
- `--categories` — Comma-separated: notes,links,sessions,tags,mocs,stale,all (default: all)
- `--digest-type` — daily, weekly, or monthly (default: daily)
- `--dry-run` — Preview snapshot without writing (default)
- `--apply` — Write snapshot to vault

Produces `Metrics-<type>-<date>.md` in `04-Archives/Metrics/snapshots/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
