---
type: index
status: active
tags:
  - project
  - index
cssclasses:
  - dashboard-beta
  - dashboard-wide
---

# 📁 Projects & Engineering Hub

<div class="project-meta-banner">
  <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
    <span class="dashboard-badge dashboard-badge-ok">🟢 Active Workspace</span>
    <span class="dashboard-badge dashboard-badge-blue">📑 Architecture Records</span>
    <span class="dashboard-badge dashboard-badge-purple">📊 Base Views</span>
  </div>
  <div style="display: flex; align-items: center; gap: 12px; font-size: 0.85em; color: var(--text-muted);">
    <span>🚀 <b>Template:</b> <code>_System/Templates/Project.md</code></span>
    <span>📊 <b>Bases View:</b> [[01-Projects/Projects.base|Projects.base]]</span>
  </div>
</div>

<div class="dashboard-kpi-strip">
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Core Vault Project</div>
    <div class="dashboard-kpi-value" style="font-size: 1.2em; color: var(--text-accent);">SETUP HUB</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">ADR Ledger</div>
    <div class="dashboard-kpi-value" style="font-size: 1.2em; color: #4facfe;">ACTIVE</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Table Filter</div>
    <div class="dashboard-kpi-value" style="font-size: 1.2em; color: #bb86fc;">PROJECTS.BASE</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Layout Standard</div>
    <div class="dashboard-kpi-value" style="font-size: 1.2em;">WIDESCREEN 2-COL</div>
  </div>
</div>

<div class="project-2col">

<div class="project-col">

<div class="dashboard-card">

### 🚀 Active Projects Directory

```dataview
TABLE status AS "Status", created AS "Created", tags AS "Tags"
FROM "01-Projects"
WHERE type = "project" AND file.name != "README"
SORT created DESC
```

> **Base view:** Open **[[01-Projects/Projects.base|Projects.base]]** for an interactive Obsidian Base table grouped by `status`.

</div>

<div class="dashboard-card">

### 📑 Architecture Decision Records (ADRs)

Key technical and operational choices reviewed by the multi-agent squad (Codex, Argus, Ledger, and Vox).

```dataview
TABLE status AS "Status", date AS "Date", deciders AS "Squad"
FROM "01-Projects/ADR"
WHERE file.name != "README"
SORT date DESC
LIMIT 5
```

- [[01-Projects/ADR/README|Open Full ADR Catalog →]]

</div>

</div>

<div class="project-col">

<div class="dashboard-card">

### 🏗️ Project Note Standard & Guidelines

One note per active repository or engineering initiative. Projects in this vault use the widescreen 2-column layout:
- **Header & KPI Strip:** Status, priority, lead agent, and repo link.
- **Left Column:** Goal & scope, repository path, technical architecture, and agent persona roles.
- **Right Column:** Operational status, interactive task checklists, linked ADR decisions, and references.

To start a new project:
1. Create a note in `01-Projects/` using `_System/Templates/Project.md`.
2. Fill in the repo URL and goal statement.
3. Track active tasks with `- [ ]` checkboxes.

</div>

<div class="dashboard-card">

### ⚡ Quick Navigation

- **Core Vault Project:** [[01-Projects/Hermes-Agent-Vault-Setup|Hermes Agent Vault Setup]]
- **Master Table:** [[01-Projects/Projects.base|Projects.base]]
- **Decision Catalog:** [[01-Projects/ADR/README|ADR Catalog]]
- **Vault Dashboard:** [[Dashboard]] · [[_System/Canvases/Dashboard-Beta|Dashboard Beta]]
- **Team Personas:** [[02-Areas/Skills/Team-Profiles-Index|Team Profiles Index]]

</div>

</div>

</div>
