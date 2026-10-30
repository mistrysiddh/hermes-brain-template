---
name: merge-duplicate
description: Find near-duplicate vault pages using Jaccard similarity scoring, flag divisive content, and atomize large notes into smaller modular units. Reports only — never auto-merges or auto-deletes.
tools:
  - repository
---

# Merge Duplicate Agent

Finds near-duplicate vault pages and helps atomize large notes into focused, modular units.

## What it does

| Feature | What it does |
|---------|-------------|
| Duplicate scan | Jaccard similarity on title + body tokens, configurable threshold |
| Divisive detection | Flags content with strong opinion markers (shouldn't auto-merge) |
| Atomize | Splits large notes by heading into smaller atomic notes |
| Report | Writes dated report to `04-Archives/Metrics/duplicates/` |

## Safety

- **Never auto-merges or auto-deletes** — all changes require human approval
- **Divisive content is flagged, not merged** — controversial topics may need separate sub-notes per perspective
- Each finding reported individually for human review

## Usage

```
@hermes-brain merge-duplicate --vault <path> scan --threshold 0.75
@hermes-brain merge-duplicate --vault <path> atomize --note 01-Projects/BigNote.md --apply
```

Options:
- `--vault` — Vault root path (required)
- `--threshold` — Similarity threshold 0-1 (default: 0.75)
- `--max-pairs` — Max pairs to report (default: 50)
- `--min-headings` — Min headings for atomize candidate (default: 5)
- `--min-size-kb` — Min size in KB for atomize candidate (default: 5)
- `--note` — Specific note to atomize (rel path from vault root)
- `--dry-run` — Preview only (default)
- `--apply` — Apply atomize with human approval

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
