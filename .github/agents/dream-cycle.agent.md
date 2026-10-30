---
name: dream-cycle
description: Autonomous cognitive reflection engine that consolidates session archives into durable knowledge — detects cross-session associations, finds architectural drift against ADRs, drafts proactive ADRs, stages memory candidates, and produces weekly synthesis reports.
tools:
  - repository
---

# Dream Cycle Agent (v2)

Autonomous cognitive reflection engine that consolidates session archives into durable semantic knowledge.

## What it does

1. **Scans recent daily sessions** (default: last 14 days)
2. **Discovers latent cross-session associations** and topic clusters
3. **Detects architectural drift & contradictions** against accepted ADRs and User Profile
4. **Auto-drafts proposed ADRs** for emerging patterns
5. **Auto-stages high-confidence durable facts** into Memory-Review for 1-click human triage
6. **Produces a Weekly Cognitive Synthesis report**: `03-Resources/Research/Weekly-Synthesis-YYYY-Www.md`
7. **Optionally inserts bilateral Obsidian wikilinks** between related sessions (`--link`)

## Subcommands

| Subcommand | What it does |
|------------|--------------|
| (default) | Full dream cycle: scan → correlate → detect drift → draft ADRs → stage memory → generate report |
| `--stage-memory` | Auto-stage distilled facts into Memory-Review for human triage |
| `--draft-adr` | Auto-draft proposed ADRs for recurring patterns |
| `--link` | Inject bilateral wikilinks between related sessions |

## Usage

```
@hermes-brain dream-cycle --vault <path> --days 14 --stage-memory --draft-adr --link
```

Produces `Weekly-Synthesis-YYYY-Www.md` in `03-Resources/Research/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
