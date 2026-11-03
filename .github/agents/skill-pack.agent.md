---
name: skill-pack
description: Skill Pack for Education — question users (tutor/Socratic mode), self-evaluate answers, and route tasks between smarter and cheaper models based on complexity. Uses DIY skill pack files in _System/SkillPacks/.
tools:
  - repository
---

# skill_pack.py — Skill Pack for Education

DIY skill packs where the second brain can question users (like a tutor), self-evaluate its own answers, and route tasks between smarter and cheaper models based on complexity.

## What it does

| Subcommand / Flag | What it does |
|-------------------|--------------|
| `--vault <path>` | Scan vault, load skill packs, generate questions, write report |
| `--topic <name>` | Topic to generate questions for (default: general) |
| `--difficulty <level>` | Question difficulty: easy, medium, hard (default: medium) |
| `--count <N>` | Number of questions to generate (default: 3) |
| `--self-eval` | Run self-evaluation on a provided answer |
| `--answer <text>` | Answer text to self-evaluate (use with --self-eval) |
| `--complexity <0.0-1.0>` | Task complexity for model routing (default: 0.5) |
| `--apply` | Write report and frontmatter to vault (default: dry-run) |
| `--test` | Run built-in self-test suite |

## Output

- **Education Skill Pack Report** (`04-Archives/Audit-Reports/Skill-Pack-Education-Report.md`): summary, skill packs, generated questions, self-evaluations, model routing decisions
- **Skill pack files** (`_System/SkillPacks/*.json`): DIY pack definitions with topics, summaries, and questions

## Model Routing

| Complexity | Model | Tier | Use Case |
|------------|-------|------|----------|
| 0.8–1.0 | claude-opus-4 | smarter | Complex reasoning, deep analysis |
| 0.5–0.79 | claude-sonnet-4 | standard | Balanced tasks |
| 0.0–0.49 | claude-haiku-3.5 | cheaper | Simple facts, quick answers |

## Usage

```
@hermes-brain skill-pack --vault <path> --topic "position mapping" --difficulty medium --count 3
@hermes-brain skill-pack --vault <path> --self-eval --answer "My answer here" --complexity 0.3
@hermes-brain skill-pack --vault <path> --apply --topic "quantum physics" --difficulty hard
```

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
