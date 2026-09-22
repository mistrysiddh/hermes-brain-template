---
layout: default
title: Note Templates Reference
nav_order: 2
has_children: false
---

# 📝 Note Templates & Schema Catalog

Hermes Brain includes 7 preconfigured note templates located in `_System/Templates/`. These templates ensure consistent metadata, structured thinking, multi-agent evaluation, and dynamic Dataview queries across your vault.

---

## 🧭 Quick Reference Matrix

| Template | File Path | Destination Folder | Frontmatter `type` | Primary Role / System |
|:---------|:----------|:-------------------|:-------------------|:----------------------|
| **Project Dashboard** | `_System/Templates/Project.md` | `01-Projects/` | `project` | Codex (Lead), Argus, Ledger, Vox |
| **Architecture Decision Record** | `_System/Templates/Architecture-Decision-Record.md` | `01-Projects/ADR/` | `adr` | 4-Agent Persona Review |
| **Lesson Learned** | `_System/Templates/Lesson-Learned.md` | `02-Areas/Skills/Lessons-Learned/` | `lesson-learned` | Argus (Safety & Risk), Self-Correction |
| **Daily Review** | `_System/Templates/Daily-Review.md` | `04-Archives/Daily/YYYY/MM/` | `daily-review` | Obsidian Daily Notes, Dataview Archiver |
| **Research Note** | `_System/Templates/Research-Note.md` | `03-Resources/Research/` | `research` | Deep Research, Literature & Tech Spikes |
| **Personality Analysis** | `_System/Templates/Personality-Judgment-Analysis.md` | `02-Areas/` or `04-Archives/Daily/` | `analysis` | Vox (Human Alignment & Cognition) |
| **Personality Dashboard** | `_System/Templates/Personality-Judgment-Dashboard.md` | `02-Areas/` or `04-Archives/Daily/` | Dynamic | Dataview & DataviewJS Telemetry |
| **Memory Review Candidate** | `04-Archives/Memory-Review/TEMPLATE.md` | `04-Archives/Memory-Review/` | Candidate | Memory Review Kanban Board |

---

## 📖 Template Specifications

### 1. Project Dashboard (`Project.md`)
- **File:** `_System/Templates/Project.md`
- **Destination:** `01-Projects/<Project-Name>.md`
- **Purpose:** Central workspace and command center for active initiatives, engineering tasks, and multi-agent coordination.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: project
  status: active      # active | completed | paused | on-hold
  created: {{date}}
  tags:
    - project
  cssclasses:
    - dashboard-beta
    - dashboard-wide
  ---
  ```
- **Key Sections:**
  - **Meta Banner & KPI Strip:** Visual badges and 4 KPI metrics (`Status`, `Priority`, `Lead Agent`, `Linked ADRs`).
  - **Executive Scope:** Core objective, user impact, and definition of done.
  - **Workspace & Branch:** Repository URL, local directory path, and target branch.
  - **Multi-Agent Squad Matrix:** Role assignments for Codex (coding), Argus (security), Ledger (tokens/cost), and Vox (documentation/alignment).
  - **Action Checklist & Linked ADRs:** Milestones and cross-references to architectural decisions.

---

### 2. Architecture Decision Record (`Architecture-Decision-Record.md`)
- **File:** `_System/Templates/Architecture-Decision-Record.md`
- **Destination:** `01-Projects/ADR/ADR-<Number>-<Title>.md`
- **Purpose:** Documents technical architecture decisions, trade-offs, and consensus across multiple agent perspectives.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: adr
  status: proposed # proposed | accepted | rejected | superseded
  date: {{date}}
  deciders: [Human, Codex, Argus, Ledger, Vox]
  tags: [adr, architecture, multi-agent]
  ---
  ```
- **Key Sections:**
  - **Context & Problem Statement:** What problem or architecture question is being addressed?
  - **Multi-Agent Persona Review:**
    - 🛡️ **Argus (Security & Risk):** Threat modeling, secret handling, attack surface.
    - ⚡ **Codex (Implementation & Performance):** Code complexity, maintainability, latency.
    - 📊 **Ledger (Resource Efficiency & Cost):** Token consumption, model inference costs, storage.
    - 🗣️ **Vox (Human Alignment & UX):** Developer ergonomics, communication clarity.
  - **Decision & Consensus:** Chosen architecture and consensus rationale.
  - **Consequences:** Positive impact vs. accepted trade-offs.

---

### 3. Lesson Learned (`Lesson-Learned.md`)
- **File:** `_System/Templates/Lesson-Learned.md`
- **Destination:** `02-Areas/Skills/Lessons-Learned/LL-<Topic>.md`
- **Purpose:** Post-incident review following agent hallucinations, API failure, tool misconfigurations, or erroneous actions.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: lesson-learned
  date: {{date}}
  agent_profile: default
  status: active
  severity: low # low | medium | high
  tags: [lesson-learned, self-correction, hermes-brain]
  ---
  ```
- **Key Sections:**
  - **1. What Happened:** Trigger prompt, intended goal, and erroneous action.
  - **2. Root Cause Analysis:** Why the failure occurred (outdated documentation, path mismatch, hallucinated flag).
  - **3. Human Correction & Fix:** How the issue was resolved.
  - **4. 🛡️ Standing Preventative Directive:** Permanent, actionable directive the agent must adhere to in all future sessions.

---

### 4. Daily Review (`Daily-Review.md`)
- **File:** `_System/Templates/Daily-Review.md`
- **Destination:** `04-Archives/Daily/YYYY/MM/DD.md` (or `YYYY-MM-DD.md`)
- **Purpose:** Daily reflection and session triage. Automatically used by Obsidian's **Daily Notes** plugin.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: daily-review
  status: draft
  created: {{date}}
  tags: [daily-review]
  ---
  ```
- **Dynamic Dataview Query:**
  Automatically queries and tables all chat sessions archived for that date:
  ```dataview
  TABLE file.mtime AS "Modified", file.size AS "Size"
  FROM "04-Archives/Daily" OR "Daily"
  WHERE (
    file.folder = this.file.folder + "/" + this.file.name
    OR file.folder = this.file.folder
    OR contains(file.folder, replace(this.file.name, "-", "/"))
  )
  AND file.name != this.file.name
  AND file.name != "README"
  AND file.name != "manifest"
  AND file.name != "Timeline"
  AND file.name != "Chat-Correlation"
  SORT file.name ASC
  ```
- **Key Sections:**
  - Dynamic Sessions Table
  - Sessions reviewed
  - Durable facts found (candidates for memory promotion)
  - Notes & follow-ups

---

### 5. Research Note (`Research-Note.md`)
- **File:** `_System/Templates/Research-Note.md`
- **Destination:** `03-Resources/Research/<Topic>.md`
- **Purpose:** Structured technical inquiries, library comparisons, security audits, and agentic workflows.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: research
  status: in-progress   # in-progress | complete | abandoned
  created: {{date}}
  tags: [research]
  ---
  ```
- **Key Sections:**
  - Question / Goal
  - Findings
  - Sources (papers, repositories, benchmarks)
  - Open threads & next questions

---

### 6. Personality Judgment Analysis (`Personality-Judgment-Analysis.md`)
- **File:** `_System/Templates/Personality-Judgment-Analysis.md`
- **Destination:** `02-Areas/Skills/` or `04-Archives/Daily/`
- **Purpose:** 12-dimension cognitive, linguistic, and behavioral alignment framework.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: analysis
  status: active
  created: {{date}}
  tags: [analysis, personality-judgment]
  subject: ""
  period: ""
  primary_style: ""
  top_hypothesis: ""
  confidence: ""
  hypotheses: []
  anomalies: []
  recommendations: []
  topic_behavior: []
  ---
  ```
- **12 Analytical Dimensions:**
  1. Subject Profile (platform, message count, data quality)
  2. Communication Style (formal, technical, assertive, casual)
  3. Language Pattern (vocabulary, sentence style, active/passive voice)
  4. Repetition Analysis (event, complaint, justification)
  5. Response Behavior (task-oriented, casual, conflict)
  6. Conversation Dynamics (initiation, topic control, questions)
  7. Conflict & Disagreement (precursors, behaviors, repair patterns)
  8. Topic Behavior (frequency, emotional expression, response time)
  9. Baseline vs. Change (shifts from standard behavior)
  10. Anomaly Detection Log (tone, latency, emoji anomalies)
  11. Context Node Summary (temporal, environmental, cultural)
  12. Hypothesis Layer with Confidence Justification (High/Med/Low percentage rationale)

---

### 7. Personality Judgment Dashboard (`Personality-Judgment-Dashboard.md`)
- **File:** `_System/Templates/Personality-Judgment-Dashboard.md`
- **Destination:** Hub note in `02-Areas/` or `04-Archives/`
- **Purpose:** Interactive Dataview and DataviewJS dashboard for visualizing behavioral telemetry, confidence distribution, active anomalies, and top hypotheses across the vault.

---

### Bonus: Memory Review Candidate (`04-Archives/Memory-Review/TEMPLATE.md`)
- **File:** `04-Archives/Memory-Review/TEMPLATE.md`
- **Destination:** `04-Archives/Memory-Review/<Candidate-Name>.md`
- **Purpose:** Staging candidate facts extracted from daily chat logs before promoting them into durable agent memory (`MEMORY.md` or `USER.md`).
- **4 Gatekeeper Criteria:**
  - **Durable:** Matters in 6+ months (not task-specific).
  - **Non-sensitive:** No secrets, credentials, or personal data.
  - **Verified:** Cited from sessions or repeated observation.
  - **Actionable:** Alters agent decision-making.

---

## 🚀 How to Use Templates in Obsidian

### Core Templates (`Ctrl+T` / `Cmd+T`)
1. Create a new note (`Ctrl+N` / `Cmd+N`).
2. Press `Ctrl+T` (or `Cmd+T` on macOS), or open the Command Palette (`Ctrl+P`) and choose **"Insert template"**.
3. Select your template from the list. Obsidian automatically populates the note and resolves `{{date}}`, `{{time}}`, and `{{title}}`.

### Daily Notes
Click the **"Open today's daily note"** ribbon icon. Obsidian creates `04-Archives/Daily/YYYY/MM/DD.md` using the `Daily-Review.md` template with the session query pre-rendered.

### Via Hermes Agent
Ask your Hermes agent in chat:
> *"Create a new Architecture Decision Record for our SQLite caching layer following `_System/Templates/Architecture-Decision-Record.md` with evaluations from Argus, Codex, Ledger, and Vox."*
