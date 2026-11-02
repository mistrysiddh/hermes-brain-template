# Hermes Brain Agent Skills

This repository contains **32+ multi-harness agent skills** for the Hermes Brain Obsidian vault template. Each skill is available as a standalone Python script in `_System/Scripts/`. Each accepts `--vault <path>` and runs in `--dry-run` mode by default. Use `--apply` to apply changes.

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

## Sub-Skill Hierarchies (v1.37–v1.44)

| Sub-Skill | File | Purpose |
|-----------|------|---------|
| **system-one** | `_System/Scripts/system_one.py` | Fast automatic agent decision support — inner monologue, four-voice council, confidence calibration, agency layer, knowledge graph, tool capture, dream cycle |
| **readability** | `_System/Scripts/readability.py` | Human readability grading — Coleman-Liau, Dale-Chall, FORCAST, PMOSE/IKIRSCH, Chinese reference |
| **social-science/humanizer** | `_System/Scripts/social_science/humanizer.py` | Prose routing, writing pattern diagnosis, sectional chunking, Turnitin mitigation, research integrity |
| **social-science/paperwork** | `_System/Scripts/social_science/paperwork.py` | Academic paper processing, citation management, bibliography formatting, paper metadata |
| **social-science/research-corpus** | `_System/Scripts/social_science/research_corpus.py` | Research source aggregation, corpus index building, reading progress tracking |
| **social-science/skill-table** | `_System/Scripts/social_science/skill_table.py` | Coherent table-of-skills merging humanizer, paperwork, research_corpus + external sources |
| **sota/profile** | `_System/Scripts/sota/profile.py` | Build repo capability profile from evidence |
| **sota/comparators** | `_System/Scripts/sota/comparators.py` | Fetch + classify comparator repos from GitHub API |
| **sota/matrix** | `_System/Scripts/sota/matrix.py` | Capability matrix + gap ranking (table-stakes vs edge) |
| **sota/report** | `_System/Scripts/sota/report.py` | Markdown report + artifact persistence for SOTA scan |
| **metrics/notes** | `_System/Scripts/metrics/notes.py` | Note-level metrics (counts, by-dir, recent, sizes) |
| **metrics/links** | `_System/Scripts/metrics/links.py` | Wikilink metrics (total, unique, broken, density) |
| **metrics/sessions** | `_System/Scripts/metrics/sessions.py` | Session metrics from Daily/ archives |
| **metrics/tags** | `_System/Scripts/metrics/tags.py` | Tag frequency distribution |
| **metrics/mocs** | `_System/Scripts/metrics/mocs.py` | MOC health (healthy vs orphaned) |
| **metrics/snapshot** | `_System/Scripts/metrics/snapshot.py` | Orchestrated dated snapshot with markdown render |
| **converse-learn/memory** | `_System/Scripts/converse_learn/memory.py` | Extract durable facts/preferences from conversations |
| **converse-learn/lesson** | `_System/Scripts/converse_learn/lesson.py` | Extract mistakes/anti-patterns from conversations |
| **converse-learn/skill** | `_System/Scripts/converse_learn/skill.py` | Extract reusable workflows from conversations |
| **converse-learn/project-doc** | `_System/Scripts/converse_learn/project_doc.py` | Extract build commands/conventions from conversations |
| **converse-learn/orchestrator** | `_System/Scripts/converse_learn/orchestrator.py` | 5-pass scan/generate/dedup/confirm/execute workflow |
| **subagents/ingestor** | `_System/Scripts/subagents/ingestor.py` | Ingest raw/ notes into vault |
| **subagents/linker** | `_System/Scripts/subagents/linker.py` | Find missing connections between notes |
| **subagents/reviewer** | `_System/Scripts/subagents/reviewer.py` | Read-only vault audit |
| **subagents/researcher** | `_System/Scripts/subagents/researcher.py` | On-demand deep research |
| **subagents/graph-analyst** | `_System/Scripts/subagents/graph_analyst.py` | Monthly navigation analysis |
| **subagents/curator** | `_System/Scripts/subagents/curator.py` | Quarterly prune/archive review |

## Using Agents

Each agent accepts `--vault <path>` and runs in `--dry-run` mode by default. Use `--apply` to apply changes.

```
python _System/Scripts/self_critique.py --vault /path/to/vault all
python _System/Scripts/auto_remediate.py --vault /path/to/vault apply
python _System/Scripts/system_one.py --vault <path> --apply monologue --days 7
python _System/Scripts/system_one.py --vault . --apply council --question "should we X?"
python _System/Scripts/system_one.py --vault . --apply providers list
python _System/Scripts/system_one.py --vault . --apply system-one research
python _System/Scripts/readability.py --vault <path> scan --days 30
python _System/Scripts/social_science/skill_table.py --vault <path> scan --days 30
python _System/Scripts/metrics/snapshot.py --vault <path> snapshot --days 30 --apply
python _System/Scripts/sota/report.py --vault <path> scan --domain agent-brain-vault --apply --save
python _System/Scripts/subagents/ingestor.py --vault <path>
python _System/Scripts/converse_learn/orchestrator.py --vault <path> scan --days 14
```

## GitHub Agents

All skills are also available as GitHub Agents in `.github/agents/`. Reference them in chat as `@hermes-brain <skill-name>`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
