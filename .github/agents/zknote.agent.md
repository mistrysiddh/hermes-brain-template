---
name: zknote
description: mikonos-style Zettelkasten skill — capture fleeting notes, convert to literature notes (atomic, one idea per note), build Map of Content (MOC) notes for recurring topics, atomize long notes into smaller units, and run network maintenance (orphan detection, weak link analysis).
tools:
  - repository
---

# zknote.py — Zettelkasten Skill

Zettelkasten note management following BASB/ZK principles — atomic, linked, networked notes.

## What it does

| Subcommand | What it does |
|------------|--------------|
| `fleeting` | Capture raw thoughts into inbox as fleeting notes |
| `literature` | Convert a fleeting note into an atomic literature note |
| `index` | Build Map of Content (MOC) notes for topics recurring across sessions |
| `split` | Atomize a long note into reusable smaller units by heading |
| `maintain` | Network maintenance: find orphaned notes and weakly linked notes |
| `all` | Run literature + index + maintain in sequence |

## Design principles

- **Atomic notes**: Each note holds one idea, linkable and reusable
- **Progressive summarization**: fleeting → literature → index
- **Networked thought**: Every note gets at least one wikilink back to its source session and forward links to related MOCs/notes
- **PARA-aware**: Respects Projects/Areas/Resources/Archives folder structure

## Usage

```
@hermes-brain zknote --vault <path> index --days 30
@hermes-brain zknote --vault <path> maintain
@hermes-brain zknote --vault <path> all
```

Produces `Self-Critique-Report.md` style report in `04-Archives/Audit-Reports/Zettelkasten-Report.md`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
