---
name: quiz
description: Test yourself from your own vault notes. Generates questions from headings (what is X?), bold text (complete the statement), and bullet points (true/false). Interactive mode with answer reveal and scoring.
tools:
  - repository
---

# Quiz Agent

Test yourself from your own vault notes. Generates quiz questions from session notes for self-testing and knowledge retention.

## Question types

| Type | Source | Example |
|------|--------|---------|
| what_is | Headings (`#`, `##`, `###`) | "What is Python Basics?" |
| complete | Bold text (`**text**`) | "Complete: Variables [...]" |
| true_false | Bullet points (`- text`) | "True or False: Lists are ordered" |

## Usage

```
@hermes-brain quiz --vault <path> --days 30 --max-per-note 5
```

Modes:
- `generate` (default): Dry-run report of questions that would be asked
- `take`: Interactive quiz with answer reveal and scoring

Options:
- `--days N` — Days of notes to scan (default: 30)
- `--max-per-note N` — Max questions per note (default: 5)

Produces a `Quiz-Report.md` in `04-Archives/Audit-Reports/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
