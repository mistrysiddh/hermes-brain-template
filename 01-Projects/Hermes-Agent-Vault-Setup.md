---
type: project
status: active
created: 2026-09-10
tags:
  - project
  - vault-meta
cssclasses:
  - dashboard-beta
  - dashboard-wide
---

# 🚀 Hermes Agent Vault Setup

<div class="project-meta-banner">
  <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
    <span class="dashboard-badge dashboard-badge-ok">🟢 Active Project</span>
    <span class="dashboard-badge dashboard-badge-blue">🏛️ PARA Vault Architecture</span>
    <span class="dashboard-badge dashboard-badge-purple">🤖 Multi-Agent Squad</span>
  </div>
  <div style="display: flex; align-items: center; gap: 12px; font-size: 0.85em; color: var(--text-muted);">
    <span>📅 <b>Created:</b> 2026-09-10</span>
    <span>🔗 <b>Upstream:</b> <a href="https://github.com/mistrysiddh/hermes-brain-template">mistrysiddh/hermes-brain-template</a></span>
  </div>
</div>

<div class="dashboard-kpi-strip">
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Project Status</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: var(--text-accent);">OPERATIONAL</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Structure Standard</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em;">PARA METHOD</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Sync Pipeline</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #4facfe;">ACTIVE (~/.hermes)</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Agent Squad</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #bb86fc;">4 SPECIALISTS</div>
  </div>
</div>

> Master hub note for **this vault itself** — its PARA folder structure, autonomous memory pipeline, multi-agent squad, and where to find current status and decisions. Referenced from [[Welcome]], [[MOC]], [[01-Projects/README|Projects/README]], [[03-Resources/README|Resources/README]], [[02-Areas/README|Areas/README]], [[SETUP]], and [[04-Archives/Memory-Review/TEMPLATE|Memory-Review/TEMPLATE]] as the one place that ties the whole layout together.

<div class="project-2col">

<div class="project-col">

<div class="dashboard-card">

### 🎯 Goal & Executive Scope

Give an AI agent (or a specialized multi-agent squad) a durable memory it cannot forget and you can actually audit and curate:
- **Transparent Staging:** Session records land as clean, readable Markdown in `04-Archives/Daily/`.
- **Sanitization & De-duplication:** Automatically stripped of secrets, tokens, and redundant noise.
- **Human-in-the-Loop:** Staged into `04-Archives/Memory-Review/` before promotion into durable memory.
- **Native Runtime Sync:** Promoted memories sync directly into Hermes agent memory (`~/.hermes/MEMORY.md` and `~/.hermes/PREAMBLE.md`).
- **Template Portability:** Upstream template updates (`update.sh` / `update.ps1`) pull fixes without touching personal notes or daily logs. See the root [[README|README]] for the full pitch.

</div>

<div class="dashboard-card">

### 🗺️ System Architecture & PARA Blueprint

| Directory | Purpose & Operational Flow |
| :--- | :--- |
| **`01-Projects/`** | Active engineering initiatives & repos, including this setup note and [[01-Projects/ADR/README\|ADR Index]]. |
| **`02-Areas/`** | Long-term standards, [[02-Areas/User-Profile\|User Profile]], and [[02-Areas/Skills/Installed-Skills-Index\|Skills Catalog]]. |
| **`03-Resources/`** | In-depth [[03-Resources/Research/README\|Research]], [[03-Resources/MOCs/Agentic-Architecture-MOC\|MOCs]], and technical manuals. |
| **`04-Archives/`** | Historical [[04-Archives/Daily/README\|Daily Sessions]], [[04-Archives/Memory-Review/Memory-Board.kanban\|Memory Review Board]], and audit reports. |
| **`_System/`** | Note [[_System/Templates/Project\|Templates]], automation [[_System/README\|Scripts]], and interactive [[_System/Canvases/Dashboard-Beta\|Canvases]]. |

</div>

<div class="dashboard-card">

### 🧠 Autonomous Memory & Cognitive Pipeline

<div style="display: flex; flex-direction: column; gap: 9px; margin: 6px 0;">
  <div style="display: flex; align-items: center; gap: 8px; font-size: 0.88em;">
    <span class="dashboard-badge dashboard-badge-ok">1. Ingestion</span>
    <span><b>Hourly Archiving:</b> <code>_System/Scripts/hourly_archive.py</code> captures sessions into <code>04-Archives/Daily/</code> with secret scrubbing.</span>
  </div>
  <div style="display: flex; align-items: center; gap: 8px; font-size: 0.88em;">
    <span class="dashboard-badge dashboard-badge-blue">2. Review</span>
    <span><b>Staging & Kanban:</b> <code>_System/Scripts/consolidate_memory.py</code> queues candidates in [[04-Archives/Memory-Review/Memory-Board.kanban|Memory-Board]].</span>
  </div>
  <div style="display: flex; align-items: center; gap: 8px; font-size: 0.88em;">
    <span class="dashboard-badge dashboard-badge-purple">3. Synthesis</span>
    <span><b>Dream Cycle:</b> <code>_System/Scripts/dream_cycle.py</code> clusters concepts into <code>03-Resources/Research/</code> syntheses.</span>
  </div>
  <div style="display: flex; align-items: center; gap: 8px; font-size: 0.88em;">
    <span class="dashboard-badge dashboard-badge-ok">4. Durable Sync</span>
    <span><b>Runtime Export:</b> <code>_System/Scripts/sync_to_hermes.py</code> compiles approved knowledge into <code>~/.hermes/MEMORY.md</code>.</span>
  </div>
</div>

</div>

<div class="dashboard-card">

### 🤖 Multi-Agent Squad & Personas

- **⚡ Codex (Lead Engineer):** Architecture, code implementation, automated script maintenance, and refactors.
- **🛡️ Argus (Security & Risk):** Secret scrubbing, API token isolation, vault privacy, and threat modeling.
- **📊 Ledger (Resource & Compute):** Token usage telemetry, context-window optimization, and cron scheduling efficiency.
- **🗣️ Vox (Human Alignment & UX):** Documentation, dashboard clarity, knowledge organization, and human reviews.

</div>

</div>

<div class="project-col">

<div class="dashboard-card">

### ⚡ Current Operational Status

- **Vault Structure:** Migrated to PARA taxonomy (`01-Projects`, `02-Areas`, `03-Resources`, `04-Archives`, `_System`).
- **Theme & Layout:** `Nemoclaw` cyber-dark theme with `dashboard-beta` widescreen styling active.
- **Active Automation:**
  - `hourly_archive.py` — Archives live conversations every hour.
  - `consolidate_memory.py` — Daily candidate extraction.
  - `sync_to_hermes.py` — Bi-directional runtime sync.
  - `dream_cycle.py` — Weekly autonomous synthesis & graph linking.
  - `vault_audit.py` — Periodic linting & health verification.

</div>

<div class="dashboard-card">

### ✅ Next Actions & Milestones

- [x] Configure base folder layout with PARA taxonomy
- [x] Implement hourly archive cron job with secret scrubbing
- [x] Set up widescreen card dashboard in `_System/Canvases/Dashboard-Beta.md`
- [x] Configure multi-agent Architecture Decision Records (`01-Projects/ADR/`)
- [x] Build Memory Review Kanban Board (`04-Archives/Memory-Review/Memory-Board.kanban`)
- [x] Deploy Bi-directional sync to Hermes runtime (`_System/Scripts/sync_to_hermes.py`)
- [x] Implement Autonomous Dream Cycle script (`_System/Scripts/dream_cycle.py`)
- [ ] Connect custom project repositories into `01-Projects/` folder
- [ ] Schedule automated weekly dream cycle via platform task scheduler / cron
- [ ] Calibrate token budget alerts in `04-Archives/Audit-Reports/Token-Usage.log`

</div>

<div class="dashboard-card">

### 📑 Durable Decisions & Architecture Records

| Record | Topic & Consensus | Status |
| :--- | :--- | :--- |
| **[[01-Projects/ADR/README\|ADR Catalog]]** | Architectural decision ledger with multi-agent consensus | `Active` |
| **Local-First Storage** | Vault remains 100% local markdown files — no external cloud dependency | `Accepted` |
| **Human-in-the-Loop** | AI memory promotion requires explicit checkbox/kanban confirmation | `Accepted` |
| **Secret Scrubbing** | All tokens, bearer auth, and private keys scrubbed before disk write | `Enforced` |
| **Bidirectional Sync** | Durable facts auto-compiled into `~/.hermes/MEMORY.md` & `PREAMBLE.md` | `Deployed` |

</div>

<div class="dashboard-card">

### 📚 Sources, Documentation & Quick Links

- **Vault Orientation:** [[Welcome]] · [[MOC]] · [[SETUP]]
- **Dashboards:** [[Dashboard|Classic Dashboard]] · [[_System/Canvases/Dashboard-Beta|Widescreen Dashboard Beta]]
- **Memory Subsystem:** [[04-Archives/Memory-Review/Memory-Board.kanban|Memory Board]] · [[04-Archives/Memory-Review/HERMES-PREAMBLE|Hermes Preamble]]
- **Skills & Telemetry:** [[02-Areas/Skills/Installed-Skills-Index|Installed Skills]] · [[04-Archives/Audit-Reports/Agent-Performance|Agent Performance]]
- **Upstream Repository:** [hermes-brain-template on GitHub](https://github.com/mistrysiddh/hermes-brain-template)

</div>

</div>

</div>
