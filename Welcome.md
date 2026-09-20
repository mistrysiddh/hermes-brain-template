---
type: index
status: active
created: 2026-08-24
tags: [hub, welcome]
---

# Welcome — Hermes Agent Vault

This is the shared Obsidian memory layer for your Hermes agent(s) —
whether that's a single agent or a small team collaborating in this vault
(see [[Skills-Notes/Team-Profiles-Index|Team-Profiles-Index]] to name and
document them, or delete that file down to one row if it's just you).

Start here: [[Projects/Hermes-Agent-Vault-Setup]] — the master hub note explaining the folder structure, the memory pipeline (Daily → Memory-Review → native memory), and current status/decisions. For topic-based browsing instead of folder-by-folder, see [[MOC]]. For a live at-a-glance view of what's active right now, see [[Dashboard]].

## Folders
- `Projects/` — one note per active project, indexed via [[Projects/README]]
- `Daily/` — raw session archive, `YYYY/MM/DD/`, exported nightly by cron
- `Research/` — active in-progress investigation notes
- `Memory-Review/` — staging area for durable facts before promotion to Hermes native memory
- `Skills-Notes/` — installed skills index + team profile index + **specialized MOCs** (Technology Stack, Cybersecurity, AI/ML, Agentic Architecture) + **Dataview Query Library** with skill analytics + **Personality Judgment Framework** (analysis framework, analysis template, dashboard, and canvas)
- `Templates/` — reusable note templates (Project, Daily-Review, Research-Note)
- `Canvases/` — visual maps (Memory Pipeline, experimental Dashboard-Beta)
- `Scripts/` — automation (consolidation, forecasting, semantic search, audit, archiving)
- `.smart-env/` — local ML embeddings, event logs, smart blocks (git-ignored)
- `.obsidian/` — Obsidian config with bundled plugins (Dataview, Smart Connections, Local REST API, Kanban)

## ✨ New & Enhanced Features
- **Specialized MOCs** — Deep-dive indexes for your core domains: [[Skills-Notes/Technology-Stack-MOC|Technology Stack]], [[Skills-Notes/Cybersecurity-MOC|Cybersecurity]], [[Skills-Notes/AI-ML-MOC|AI/ML Workflows]], [[Skills-Notes/Agentic-Architecture-MOC|Agentic Architecture]]
- **Personality Judgment Framework** — Structured method for analyzing communication patterns and traits (framework, analysis template, dashboard, and canvas)
- **Skill Usage Analytics** — Dataview queries for skill frequency, project cross-referencing, velocity, memory retention ([[Skills-Notes/Dataview-Query-Library#Skill-Usage-Analytics]])
- **Enhanced Skill Forecasting** — CLI flags (`--days`, `--top`, `--debug`, `--no-log`), recency weighting, gap analysis, complementary skills (`Scripts/skill_forecast.py`)
- **Semantic Search Layer** — Local vector search with HTTP server for Dashboard widget (`Scripts/semantic_search.py --serve`)
- **Smart Blocks** — Reusable templates in `.smart-env/smart_blocks/`: decision matrices, troubleshooting flows, reference architectures, code snippets
- **External Tag→Skill Mapping** — Editable `Scripts/tag_skill_map.json` for custom skill discovery
- **Template Update System** — Safe git-based pulls from template repo with conflict resolution (`Scripts/Installers/update.sh`)

## Quick Start
1. Run the installer: `./Scripts/Installers/install.sh` (or `install.ps1` on Windows)
2. Open the vault in Obsidian and enable the 4 bundled community plugins
3. Set `HERMES_VAULT_PATH` in Hermes: `hermes config set env.HERMES_VAULT_PATH "<vault-path>"`
4. Run `python Scripts/consolidate_memory.py "<vault-path>"` as a sanity check
5. Schedule `hourly_archive.py` via cron/Task Scheduler for session archiving

Do not store secrets/API keys as plaintext notes in this vault — it syncs via OneDrive. Use Hermes's protected `.env` (`hermes config set env.KEY_NAME "..."`) instead.
