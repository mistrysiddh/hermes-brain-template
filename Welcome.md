---
type: index
status: active
created: 2026-08-24
tags: [hub, welcome]
---

# Welcome — Hermes Agent Vault

This is the shared Obsidian memory layer for your Hermes agent(s) — whether that's a single agent or a small team collaborating in this vault (see [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] to name and document them, or customize down to one row if it's just you).

Start here: [[01-Projects/Hermes-Agent-Vault-Setup]] — the master hub note explaining the vault architecture, the memory pipeline (Daily → Memory-Review → native memory), and current decisions. For topic-based browsing across domains, see [[MOC]]. For a live at-a-glance view of what's active right now, open [[Dashboard]] or the widescreen card view at [[_System/Canvases/Dashboard-Beta|Dashboard-Beta]].

## 📁 PARA Architecture
The vault is structured according to the **PARA Method** (Projects, Areas, Resources, Archives) with a dedicated `_System` core:

- `01-Projects/` — Active projects with defined deadlines/outcomes, ADRs, and [[01-Projects/Projects.base|Projects Database]] (see [[01-Projects/README|01-Projects Index]])
- `02-Areas/` — Ongoing domains of responsibility, [[02-Areas/User-Profile|User-Profile]] (human alignment parameters), and [[02-Areas/README|Areas Index]]
- `03-Resources/` — Topics of ongoing interest, [[03-Resources/Research/README|Research Inquiries]], and [[03-Resources/README|Resources Index]]
- `04-Archives/` — Inactive or completed items: [[04-Archives/Daily/README|Daily Session Archives]], [[04-Archives/Memory-Review/Memory-Board.kanban|Memory Review Board]], and [[04-Archives/README|Archives Index]]
- `_System/` — Vault mechanics: Reusable templates in `_System/Templates/`, automation tools in `_System/Scripts/`, visual canvases in `_System/Canvases/`, and [[_System/README|System Index]]

## ✨ Core Features & Enhancements
- **Domain Knowledge Hubs (MOCs)** — Deep-dive topical indexes: [[03-Resources/MOCs/Technology-Stack-MOC|Technology Stack]], [[03-Resources/MOCs/Cybersecurity-MOC|Cybersecurity]], [[03-Resources/MOCs/AI-ML-MOC|AI/ML Workflows]], [[03-Resources/MOCs/Agentic-Architecture-MOC|Agentic Architecture]]
- **Personality Judgment Framework** — 11-dimension behavioral analysis framework, analysis template, dashboard, and canvas in `02-Areas/Skills/` and `_System/`
- **Memory Consolidation & Promotion** — 3-stage visual board at [[04-Archives/Memory-Review/Memory-Board.kanban|Memory-Board]] with automated distillation via `_System/Scripts/dream_cycle.py`
- **Telemetry & Skill Analytics** — Token logging, session correlation, and skill forecasting via `_System/Scripts/hourly_archive.py` and `_System/Scripts/skill_forecast.py`
- **Semantic Vector Layer** — Local embeddings and search via `_System/Scripts/semantic_search.py`
- **Widescreen Dashboard** — Card-based dashboard with live clock, KPI strip, session heatmap, calendar, and quick-launch actions at [[_System/Canvases/Dashboard-Beta|Dashboard-Beta]]

## 🚀 Quick Start
1. Open the vault in Obsidian and verify the community plugins (Dataview, Smart Connections, Kanban)
2. Set your `HERMES_VAULT_PATH` in Hermes CLI: `hermes config set env.HERMES_VAULT_PATH "<vault-path>"`
3. Personalize your operating parameters in [[02-Areas/User-Profile|User-Profile.md]]
4. Run a sanity check sync: `python _System/Scripts/sync_to_hermes.py --dry-run`
5. Schedule `_System/Scripts/hourly_archive.py` via cron / Task Scheduler for background session archiving

Do not store secrets/API keys as plaintext notes in this vault — it syncs via cloud storage. Use Hermes's protected environment variables instead.
