---
name: converse-learn
description: aprende-style self-improvement from sessions. Reviews archived session notes and extracts learnings across four categories (memory, lesson, skill, project-doc). Confirmation-first — never auto-writes. Each learning gets its own file in Memory-Review with frontmatter and is appended to MEMORY.md.
tools:
  - repository
---

# converse_learn.py — Conversation Learning Skill

Aprende-style self-improvement skill that reviews archived session notes and extracts durable learnings.

## What it does

Scans session archives and extracts learnings across four categories:

| Category | What it captures | Lives in |
|----------|-----------------|----------|
| memory | Durable facts, preferences, project context, external references | `04-Archives/Memory-Review/` |
| lesson | Mistakes that happened — what, why, and how to avoid (anti-pattern) | `04-Archives/Memory-Review/` |
| skill | Reusable multi-step workflow surfaced from repeated patterns | `04-Archives/Memory-Review/` |
| project-doc | Build commands, repo conventions, gotchas worth documenting | `04-Archives/Memory-Review/` |

## 5-Pass Workflow

1. **Scan** — Parse session notes for corrections, error→fix sequences, repeated attempts, why-explanations, and step-by-step workflows
2. **Generate** — Convert each signal into a candidate learning with title, rationale, confidence, and source
3. **Dedup** — Check against existing Memory-Review entries without silently dropping; annotate overlaps
4. **Confirm** — Present candidates one at a time for human approval (`y/n/edit/skip`)
5. **Execute** — Write confirmed learnings to `Memory-Review/` and append to `MEMORY.md` index

## Usage

```
@hermes-brain converse_learn --vault <path> --days 14 scan
@hermes-brain converse_learn --vault <path> --days 14 apply
```

Options:
- `--vault` — Vault root path (required)
- `--days N` — Days of sessions to scan (default: 14)
- `--dry-run` — Preview findings without applying (default)
- `--apply` — Apply confirmed learnings with per-item approval
- `--test` — Run built-in self-test suite

Produces `Self-Critique-Report.md` in `04-Archives/Audit-Reports/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
