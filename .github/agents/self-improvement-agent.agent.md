---
name: self-improvement-agent
description: Self-improving agent architectures — task complexity router (small vs large model), self-evaluation loop, skill forge / command tracker, and orchestrator pattern for multi-model agent systems.
tools:
  - repository
---

# Self-Improvement Agent Architectures Agent

Implements self-improving agent patterns where smaller models handle grunt work
while larger models strategize and orchestrate. Based on research from
pskoett/self-improving-agent, Git-on-my-level/self-improving-agent-ecosystem,
and GodModeAI2025/skill-forge.

## Subcommands

| Subcommand | What it does |
|------------|-------------|
| route | Classify a task as grunt (small model) or orchestrate (large model) |
| evaluate | Self-evaluate agent output across 5 quality dimensions |
| track | Track command/skill usage for improvement analytics |
| forge | Run skill forge cycle — evaluate, improve, version |

## Model allocation principle

- **Small models**: grunt work — formatting, extraction, summarization, cleanup
- **Large models**: orchestration — planning, evaluation, strategy, quality gates
- Evaluation output feeds back into improvement cycles

## Usage

```
@hermes-brain self-improvement-agent --vault <path> route --task "Format this markdown file"
@hermes-brain self-improvement-agent --vault <path> evaluate --output "Agent output text" --context "task context"
@hermes-brain self-improvement-agent --vault <path> track --command "my_cmd" --tier small --duration 1.5
@hermes-brain self-improvement-agent --vault <path> forge --skill "my_skill" --skill-file skill.md --focus clarity
```

Options:
- `--vault` — Vault root path (required)
- `--task` — Task description to route (for route)
- `--output` — Agent output to evaluate (for evaluate)
- `--context` — Task context for evaluation (optional)
- `--command` — Command name to track (for track)
- `--success` / `--failure` — Command outcome (for track)
- `--duration` — Duration in seconds (for track)
- `--tier` — Model tier used: small or large (for track)
- `--skill` — Skill name (for forge)
- `--skill-file` — Path to skill content file (for forge)
- `--focus` — Improvement focus area (for forge, default: general)
- `--save` — Save report to vault
- `--dry-run` — Preview only (default)
- `--apply` — Write report to vault

Writes reports to `04-Archives/Self-Improvement/` and tracks commands in `04-Archives/Self-Improvement/skill-registry.json`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
