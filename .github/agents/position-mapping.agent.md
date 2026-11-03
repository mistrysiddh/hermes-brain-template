---
name: position-mapping
description: Position mapping skill — maps each note's position in vault hierarchy (folder depth, parent MOC, incoming/outgoing link counts, orphan detection, position scoring). Produces a dated position map report and optionally injects position frontmatter into notes.
tools:
  - repository
---

# position_mapping.py — Position Mapping Skill

Maps every note's position in the vault hierarchy — folder depth, nearest parent MOC, incoming/outgoing wikilink counts, orphan detection, and a position score. Generates a dated report and optionally writes `position:` and `position_score:` frontmatter into notes.

## What it does

| Subcommand | What it does |
|------------|--------------|
| `--vault <path>` (dry-run) | Scan vault, build position map, write report to `04-Archives/Audit-Reports/Position-Map-Report.md` |
| `--vault <path> --apply` | Same as dry-run, plus inject `position:` and `position_score:` frontmatter into notes missing it |
| `--test` | Run built-in self-test suite |

## Output

- **Position Map Report** (`04-Archives/Audit-Reports/Position-Map-Report.md`): summary stats, depth/tier distribution, hub notes, orphaned notes, full position map table
- **Frontmatter injection** (`--apply` only): adds `position: <tier>` and `position_score: <score>` to notes missing them

## Position Tiers

| Tier | Criteria |
|------|----------|
| root | Vault root (depth 0) |
| hub | 10+ total links |
| connector | 3–9 total links |
| leaf | 1–2 total links |
| orphan | No links, no parent frontmatter |

## Usage

```
@hermes-brain position-mapping --vault <path>
@hermes-brain position-mapping --vault <path> --apply
@hermes-brain position-mapping --vault <path> --test
```

Produces `Position-Map-Report.md` in `04-Archives/Audit-Reports/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
