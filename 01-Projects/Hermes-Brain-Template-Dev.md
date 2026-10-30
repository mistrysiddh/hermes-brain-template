---
type: project
status: active
created: 2026-10-29
tags:
  - project
  - vault-meta
  - template-dev
cssclasses:
  - dashboard-beta
  - dashboard-wide
---

# 🏗️ Hermes Brain Template Dev

<div class="project-meta-banner">
  <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
    <span class="dashboard-badge dashboard-badge-ok">🟢 Active Project</span>
    <span class="dashboard-badge dashboard-badge-blue">📦 Template Product</span>
    <span class="dashboard-badge dashboard-badge-purple">🤖 Multi-Agent Skills</span>
  </div>
  <div style="display: flex; align-items: center; gap: 12px; font-size: 0.85em; color: var(--text-muted);">
    <span>📅 <b>Created:</b> 2026-10-29</span>
    <span>🔗 <b>Upstream:</b> <a href="https://github.com/mistrysiddh/hermes-brain-template">mistrysiddh/hermes-brain-template</a></span>
  </div>
</div>

<div class="dashboard-kpi-strip">
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Project Status</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: var(--text-accent);">ACTIVE</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Template Version</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em;">v1.24.9</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Agent Skills</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #4facfe;">14+ SKILLS</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">CI/CD</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #bb86fc;">SYNTAX + DRIFT</div>
  </div>
</div>

> Master hub note for **template development itself** — tracking the Hermes Brain template as a product: releases, agent skills, CI/CD, website, and the multi-agent decision framework. This is where we plan what to build next for the template, track skills in development, and record architectural decisions about the template product itself. Referenced from [[Hermes-Agent-Vault-Setup|Hermes Agent Vault Setup]], [[Dashboard]], [[README|README]], and [[03-Resources/Axioms|Axioms]].

---

### 🎯 Goal & Executive Scope

Treat the Hermes Brain template as a product: a reusable, versioned, multi-agent-compatible Obsidian vault template that gives any AI agent (Hermes, OpenClaw, Claude Code, Cursor, etc.) a persistent, auditable, human-controlled memory system.

**In scope:**
- **Agent skills:** self-critique, auto-remediation, knowledge synthesis, dream cycle, vault audit, session snapshot, cron migration, template drift
- **CI/CD:** syntax checks, secret scanning, template drift, smoke tests on every push
- **Website:** the showcase site at mistrysiddh.github.io/hermes-brain-template/
- **Releases:** tagged releases with changelogs (v1.24.0 → v1.24.9)
- **Multi-agent architecture:** Decisions/Principles/Axioms + ADR process

**Out of scope:**
- Personal vault content (Daily/, Memory-Review/, Research/ — gitignored by design)
- Individual user's notes and chats
- Proprietary AI model hosting

---

### 🗺️ PARA Mapping

| Directory | Purpose in Template Dev |
|-----------|------------------------|
| **`01-Projects/`** | This project charter + ADRs for template decisions |
| **`02-Areas/`** | Installed skills catalog, skill-to-chat links, user profile |
| **`03-Resources/`** | Research notes, MOCs, synthesis outputs, weekly reports |
| **`04-Archives/`** | Daily session archives, memory review board, audit reports |
| **`_System/`** | Templates, automation scripts, interactive canvases |

---

### 🧠 Multi-Agent Squad & Personas

Same squad as the vault setup, scoped to template product decisions:

- **⚡ Codex (Lead Engineer):** Template scripts, CI/CD workflows, skill refactors, website HTML/CSS/JS
- **🛡️ Argus (Security & Risk):** Secret scanning, personal-data-guard CI, vault privacy audits
- **📊 Ledger (Resource & Compute):** Token usage telemetry, context-window optimization, release sizing
- **🗣️ Vox (Human Alignment & UX):** Documentation, dashboard clarity, issue triage, user-facing README

---

### ⚡ Current Operational Status

- **Template Version:** v1.24.9 (tagged & released)
- **Releases:** v1.24.0 through v1.24.9 on GitHub
- **Agent Skills (14+):** self_critique.py, auto_remediate.py, knowledge_synthesis.py, dream_cycle.py, vault_audit.py, session_git_snapshot.py, migrate_cron_sessions.py, consolidate_memory.py, promote_memory.py, skill_forecast.py, template_drift.py, agent_performance.py, hermes_brain_mcp.py, semantic_search.py
- **CI/CD:** lint.yml (bash/Python/PowerShell syntax + smoke tests), personal-data-guard.yml (personal content blocker), NEW: self-critique/auto-remediate/knowledge-synthesis/dream-cycle/template-drift/secret-scan jobs
- **Website:** Deployed via GitHub Pages (deploy-pages.yml)

---

### ✅ Next Actions & Milestones

- [x] v1.24.0 — Decision Log, Principles, Axioms & Local Git Safety Net
- [x] v1.24.1 — Remove personal data leaked into template files
- [x] v1.24.2 — Stop Dashboard.md from crashing Obsidian
- [x] v1.24.3 — Multi-Harness Skill Refactors
- [x] v1.24.4 — Knowledge Synthesis skill made multi-harness portable
- [x] v1.24.5 — Knowledge Synthesis skill (BASB/ZK)
- [x] v1.24.6 — Self-Critique skill for vault health audit
- [x] v1.24.7 — Self-Critique skill for multi-harness agents
- [x] v1.24.8 — Auto-Remediation skill for multi-harness agents
- [x] v1.24.9 — Knowledge Synthesis phase (BASB/ZK) complete
- [ ] CI/CD: Add release automation (auto-changelog from conventional commits)
- [ ] CI/CD: Add template drift auto-fix (not just detection)
- [ ] CI/CD: Add secret-scanning pre-commit gate
- [ ] Website: Add contributor credits (TomLucidor featured in footer)
- [ ] Phase 4: Pick next skill from issue #11 gap analysis (quiz / merge duplicate / metrics / unstuck-decide / subagents / radar / onboarding)

---

### 📑 Durable Decisions & Architecture Records

| Record | Topic & Consensus | Status |
|--------|-------------------|--------|
| **[[01-Projects/ADR/README\|ADR Catalog]]** | Architectural decision ledger with multi-agent consensus | `Active` |
| **Local-First Storage** | Vault remains 100% local markdown files — no external cloud dependency | `Accepted` |
| **Human-in-the-Loop** | AI memory promotion requires explicit checkbox/kanban confirmation | `Accepted` |
| **Secret Scrubbing** | All tokens, bearer auth, and private keys scrubbed before disk write | `Enforced` |
| **Bidirectional Sync** | Durable facts auto-compiled into `~/.hermes/MEMORY.md` & `PREAMBLE.md` | `Deployed` |
| **Multi-Harness Skills** | All agent skills accept `--vault` CLI arg, deferred path resolution, stdlib-only | `Accepted` |
| **Dry-Run by Default** | All mutating skills run in dry-run mode unless `--apply` is passed | `Accepted` |

---

### 📚 Sources, Documentation & Quick Links

- **Vault Orientation:** [[Welcome]] · [[MOC]] · [[SETUP]]
- **Dashboards:** [[Dashboard|Classic Dashboard]] · [[_System/Canvases/Dashboard-Beta|Widescreen Dashboard Beta]]
- **Memory Subsystem:** [[04-Archives/Memory-Review/Memory-Board.kanban|Memory Board]] · [[04-Archives/Memory-Review/HERMES-PREAMBLE|Hermes Preamble]]
- **Skills & Telemetry:** [[02-Areas/Skills/Installed-Skills-Index|Installed Skills]] · [[04-Archives/Audit-Reports/Agent-Performance|Agent Performance]]
- **Upstream Repository:** [hermes-brain-template on GitHub](https://github.com/mistrysiddh/hermes-brain-template)
- **Releases:** [GitHub Releases](https://github.com/mistrysiddh/hermes-brain-template/releases)
- **Issue #11 — Multi-Harness Agent Skills:** [Follow-up issue with feature backlog](https://github.com/mistrysiddh/hermes-brain-template/issues/11)
