---
name: prompt-quality
description: Prompt quality checker — analyzes prompts for clarity, specificity, actionability, structure, and completeness. Produces a 0-100 score with improvement suggestions. Can scan vault for all prompts or check a single prompt.
tools:
  - repository
---

# Prompt Quality Agent

Analyzes prompts for quality preservation across models. Scores on 5 dimensions and provides improvement suggestions.

## Dimensions scored

| Dimension | What it measures |
|-----------|-----------------|
| Clarity | Intent and expected output clarity |
| Specificity | Requirements, constraints, format details |
| Actionability | Can be acted on without clarification |
| Structure | Headings, lists, code blocks, tables |
| Completeness | Context, task, constraints, audience, tone |

## Usage

```
@hermes-brain prompt-quality --vault <path> check --prompt "Your prompt text"
@hermes-brain prompt-quality --vault <path> check --prompt-file /path/to/prompt.md --save
@hermes-brain prompt-quality --vault <path> scan --save
```

Options:
- `--vault` — Vault root path (required)
- `--prompt` — Prompt text to analyze (for check)
- `--prompt-file` — Path to a file containing the prompt (for check)
- `--save` — Save report to vault
- `--dry-run` — Preview report without writing (default)
- `--apply` — Write report to vault

Writes reports to `04-Archives/Metrics/prompt-quality/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
