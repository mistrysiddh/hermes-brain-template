---
name: unstuck-decide
description: Roadblock antidote + decision workflow. Unstuck mode analyzes a roadblock situation and suggests structured antidotes across 6 categories. Decide mode runs pros/cons, 2x2 impact-effort matrix, or weighted criteria scoring. Reports only — never auto-decides.
tools:
  - repository
---

# Unstuck + Decide Agent

Roadblock antidote and structured decision workflow for the Hermes Brain vault.

## Unstuck mode

Analyzes a roadblock and suggests antidotes across 6 categories:

| Category | When to use |
|----------|-------------|
| starting | Can't begin a task |
| stuck_middle | Started but stalled |
| overwhelmed | Too much to do, don't know where to focus |
| blocked | External dependency blocking progress |
| perfectionism | Can't finish because it's not "perfect" |
| unclear | Don't know what the next step is |

Auto-detects category from keywords, or accepts `--category` explicitly.

## Decide mode

Three decision methods:

| Method | What it does |
|--------|-------------|
| pros_cons | Simple pros/cons list with net scoring |
| matrix_2x2 | Impact vs effort 2×2 matrix with quadrant classification |
| weighted | Weighted criteria scoring with percentage |

## Usage

```
@hermes-brain unstuck-decide --vault <path> unstuck --situation "I'm blocked waiting for API access" --category blocked
@hermes-brain unstuck-decide --vault <path> decide --method matrix_2x2 --options-file options.json --save
```

Options:
- `--vault` — Vault root path (required)
- `--situation` — Describe the roadblock (for unstuck)
- `--category` — Unstuck category (optional, auto-detected if omitted)
- `--method` — pros_cons, matrix_2x2, or weighted (default: pros_cons)
- `--options-file` — JSON file with options data (for decide)
- `--criteria-file` — JSON file with weighted criteria (for weighted method)
- `--save` — Save analysis/decision to vault

Saves unstuck analyses to `01-Projects/Unstuck/` and decisions to `03-Resources/Decisions/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
