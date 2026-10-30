# Hermes Brain Agent Skills

This repository contains **7 multi-harness agent skills** for the Hermes Brain Obsidian vault template. Each skill is available as a GitHub Agent in `.github/agents/` and as a standalone Python script in `_System/Scripts/`.

## Agent Skills

| Agent | File | Purpose |
|-------|------|---------|
| **self-critique** | `_System/Scripts/self_critique.py` | Vault health audit — broken wikilinks, missing frontmatter, module-level paths, hardcoded paths, secret exposure |
| **auto-remediate** | `_System/Scripts/auto_remediate.py` | Apply safe fixes from Self-Critique findings (missing `--vault`, missing frontmatter, broken links) |
| **knowledge-synthesis** | `_System/Scripts/knowledge_synthesis.py` | BASB/ZK knowledge consolidation — atomic ideas, progressive summarization, MOCs, backlinks |
| **dream-cycle** | `_System/Scripts/dream_cycle.py` | Cognitive reflection — cross-session associations, drift detection, ADR drafting, memory staging |
| **quiz** | `_System/Scripts/quiz.py` | Self-testing from vault notes — what is X?, complete the statement, true/false |
| **radar** | `_System/Scripts/radar.py` | Standing surveillance on sources (blogs, news, papers) → daily/weekly digest |
| **metrics** | `_System/Scripts/metrics.py` | Dated vault metrics snapshot — notes, links, sessions, tags, MOCs, stale |
| **converse-learn** | `_System/Scripts/converse_learn.py` | Conversation learning — extract learnings from sessions across 4 categories |
| **zknote** | `_System/Scripts/zknote.py` | Zettelkasten — fleeting notes, literature notes, MOCs, note splitting, network maintenance |

## Using Agents

Each agent accepts `--vault <path>` and runs in `--dry-run` mode by default. Use `--apply` to apply changes.

```
python _System/Scripts/self_critique.py --vault /path/to/vault all
python _System/Scripts/auto_remediate.py --vault /path/to/vault apply
python _System/Scripts/knowledge_synthesis.py --vault /path/to/vault --moc --atomic --link
python _System/Scripts/dream_cycle.py --vault /path/to/vault --stage-memory --draft-adr --link
python _System/Scripts/quiz.py --vault /path/to/vault --days 30
python _System/Scripts/radar.py --vault /path/to/vault --days 7 scan
python _System/Scripts/radar.py --vault /path/to/vault --days 7 digest --apply
python _System/Scripts/metrics.py --vault /path/to/vault --days 30 snapshot
python _System/Scripts/metrics.py --vault /path/to/vault --days 30 snapshot --apply
python _System/Scripts/converse_learn.py --vault /path/to/vault --days 14
python _System/Scripts/zknote.py --vault /path/to/vault index --days 30
```

## GitHub Agents

All 7 skills are also available as GitHub Agents in `.github/agents/`. Reference them in chat as `@hermes-brain <skill-name>`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
