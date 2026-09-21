---
type: index
status: active
tags:
  - adr
  - architecture
  - index
cssclasses:
  - dashboard-beta
  - dashboard-wide
---

# 📑 Multi-Agent Architecture Decision Records (ADR)

<div class="project-meta-banner">
  <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
    <span class="dashboard-badge dashboard-badge-ok">🟢 ADR Catalog Active</span>
    <span class="dashboard-badge dashboard-badge-blue">🏛️ Architectural Consensus</span>
    <span class="dashboard-badge dashboard-badge-purple">🤖 4-Agent Persona Review</span>
  </div>
  <div style="display: flex; align-items: center; gap: 12px; font-size: 0.85em; color: var(--text-muted);">
    <span>🚀 <b>Template:</b> <code>_System/Templates/Architecture-Decision-Record.md</code></span>
    <span>📁 <b>Parent:</b> [[01-Projects/README|Projects]]</span>
  </div>
</div>

<div class="project-2col">

<div class="project-col">

<div class="dashboard-card">

### 📋 Architectural Decision Log

Index of technical architecture and operational decisions evaluated by the multi-agent team (Human + Codex, Argus, Ledger, and Vox).

```dataview
TABLE status AS "Status", date AS "Date", deciders AS "Squad"
FROM "01-Projects/ADR"
WHERE file.name != "README"
SORT date DESC
```

> **Template:** When proposing a major architectural change or technical decision, instantiate `_System/Templates/Architecture-Decision-Record.md`.

</div>

</div>

<div class="project-col">

<div class="dashboard-card">

### 🤖 Evaluator Persona Roles

- **⚡ Codex (Implementation & Performance):** Technical architecture, maintainability, execution latency, and backward compatibility.
- **🛡️ Argus (Security & Threat Boundary):** Credential protection, secret scrubbing, sandbox isolation, and threat modeling.
- **📊 Ledger (Resource & Compute Economics):** Token consumption, context retention overhead, model inference cost, and cron load.
- **🗣️ Vox (Human Alignment & UX):** Developer ergonomics, prompt clarity, documentation completeness, and UI/UX design.

</div>

<div class="dashboard-card">

### ⚡ Quick Links & Navigation

- **Parent Hub:** [[01-Projects/README|Projects Overview]]
- **Vault Setup Project:** [[01-Projects/Hermes-Agent-Vault-Setup|Hermes Agent Vault Setup]]
- **Memory Kanban:** [[04-Archives/Memory-Review/Memory-Board.kanban|Memory Review Board]]
- **Self-Correction Catalog:** [[02-Areas/Skills/Lessons-Learned/README|Lessons Learned]]

</div>

</div>

</div>
