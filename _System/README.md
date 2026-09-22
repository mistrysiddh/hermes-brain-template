---
type: index
status: active
tags:
  - para
  - system
cssclasses:
  - dashboard-beta
  - dashboard-wide
---

# ⚙️ _System & Automation Infrastructure

Operational machinery, automation engines, visual canvases, note templates, and internal assets powering the Hermes Brain vault.

<div class="dashboard-kpi-strip">
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Note Schemas</div>
    <div class="dashboard-kpi-value" style="font-size: 1.2em; color: var(--text-accent);">TEMPLATES</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Automations</div>
    <div class="dashboard-kpi-value" style="font-size: 1.2em; color: #4facfe;">SCRIPTS</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Visual Dashboards</div>
    <div class="dashboard-kpi-value" style="font-size: 1.2em; color: #bb86fc;">CANVASES</div>
  </div>
</div>

<div class="project-2col">

<div class="project-col">

<div class="dashboard-card">

### 📝 Templates & Note Schemas

*👉 Full Documentation: [[_System/Templates/README|Templates Catalog & Field Reference]]*

Located in `_System/Templates/`:
- **[[_System/Templates/Project|Project Template]]:** Widescreen 2-column project dashboard.
- **[[_System/Templates/Architecture-Decision-Record|ADR Template]]:** 4-agent persona evaluation framework.
- **[[_System/Templates/Lesson-Learned|Lesson Learned Template]]:** Post-mortem and prevention schema.
- **[[_System/Templates/Daily-Review|Daily Review Template]]:** Evening reflection and session audit.
- **[[_System/Templates/Research-Note|Research Note Template]]:** Structured investigation brief.
- **[[_System/Templates/Personality-Judgment-Analysis|Personality Judgment Analysis]]:** 7-dimension cognitive evaluation.
- **[[_System/Templates/Personality-Judgment-Dashboard|Personality Judgment Dashboard]]:** Dataview KPI tracker and cross-session matrix.

</div>

<div class="dashboard-card">

### 💻 Scripts & Automation Engines

Located in `_System/Scripts/`:
- **`hourly_archive.py`:** Conversation archiver with automated secret scrubbing.
- **`consolidate_memory.py`:** Daily fact candidate extractor and deduplicator.
- **`sync_to_hermes.py`:** Bi-directional sync engine exporting knowledge to `~/.hermes/MEMORY.md`.
- **`dream_cycle.py`:** Offline associative memory clustering and weekly synthesis generator.
- **`vault_audit.py`:** Comprehensive linter checking broken links, orphans, and stale items.
- **`session_tagger.py` / `skill_forecast.py` / `agent_performance.py`:** Telemetry and tracking engines.

</div>

</div>

<div class="project-col">

<div class="dashboard-card">

### 🎨 Visual Canvases & Dashboards

Located in `_System/Canvases/`:
- **[[_System/Canvases/Dashboard-Beta|Dashboard-Beta]]:** 12-block responsive widescreen command center.
- **`Memory-Pipeline.canvas`:** Visual map of the raw ingestion → staging → durable memory flow.
- **`Personality-Judgment-Canvas.canvas`:** Cognitive analysis matrix.

</div>

<div class="dashboard-card">

### 🧭 Navigation

- 📁 **[[01-Projects/README|01 - Projects]]** — Active initiatives & ADRs
- 🌿 **[[02-Areas/README|02 - Areas]]** — User Profile & Skills
- 📚 **[[03-Resources/README|03 - Resources]]** — Research, MOCs & Guides
- 📦 **[[04-Archives/README|04 - Archives]]** — Daily sessions & Memory staging

</div>

</div>

</div>
