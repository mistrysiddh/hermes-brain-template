---
name: pm-skills-examination
description: Deconstructs PM skill pack features from external repos, compares across repos, produces self-reports per skill, and synthesizes findings. Based on research from phuryn/pm-skills and mohitagw15856/pm-claude-s.
tools:
  - repository
---

# PM Skills Examination Agent

Deconstructs PM skill pack features from external repositories, compares them
across repos, produces per-skill self-reports, and synthesizes findings.

Based on research from:
- phuryn/pm-skills — 69 PM skills, 42 chained workflows, 9 plugins
- mohitagw15856/pm-claude-skills — 1314 Agent Skills (plain-markdown SKILL.md)

## Subcommands

| Subcommand | What it does |
|------------|-------------|
| examine | Deconstruct a skill pack repo — extracts skill metadata, features, structural patterns |
| compare | Compare two repos side by side — structural patterns, feature overlap, workflow chains |
| synthesize | Synthesize findings into a self-report with key observations and Hermes Brain recommendations |

## Usage

```
@hermes-brain pm-skills-examination --vault <path> examine --repo-name "phuryn/pm-skills" --skills-dir /path/to/skills
@hermes-brain pm-skills-examination --vault <path> compare --repo-a "phuryn/pm-skills" --summary-a summary-a.json --repo-b "mohitagw15856/pm-claude-skills" --summary-b summary-b.json
@hermes-brain pm-skills-examination --vault <path> synthesize --summary-a summary-a.json --summary-b summary-b.json --save
```

Options:
- `--vault` — Vault root path (required)
- `--repo-name` — Name of the repo being examined (for examine)
- `--skills-dir` — Path to skills directory containing SKILL.md files (for examine)
- `--repo-a` / `--repo-b` — Repo names for comparison (for compare/synthesize)
- `--summary-a` / `--summary-b` — JSON files with repo summaries (for compare/synthesize)
- `--save` — Save report to vault
- `--dry-run` — Preview report without writing (default)
- `--apply` — Write report to vault

Writes reports to `04-Archives/Metrics/pm-skills-examination/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
