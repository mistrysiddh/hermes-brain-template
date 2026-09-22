---
type: index
status: active
tags:
  - para
  - system
  - templates
cssclasses:
  - dashboard-beta
  - dashboard-wide
---

# 📝 Templates & Schema Reference Catalog

Central documentation and reference guide for all Obsidian note templates powering the Hermes Brain vault.

> [!TIP] View & Copy Raw Source Code
> Looking to see the actual raw markdown source code or copy templates in 1 click? Open **[[_System/Templates/Template-Showcase|Template-Showcase.md]]** for collapsible raw markdown blocks with syntax highlighting!

<div class="project-meta-banner">
  <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
    <span class="dashboard-badge dashboard-badge-ok">7 Core Templates</span>
    <span class="dashboard-badge dashboard-badge-purple">PARA Method Aligned</span>
    <span class="dashboard-badge dashboard-badge-blue">Multi-Agent Squad Aware</span>
    <span class="dashboard-badge dashboard-badge-orange">Dataview Ready</span>
  </div>
  <div style="display: flex; align-items: center; gap: 12px; font-size: 0.85em; color: var(--text-muted);">
    <span>📁 <b>Templates Folder:</b> <code>_System/Templates/</code></span>
    <span>⚙️ <b>Config:</b> <code>.obsidian/templates.json</code></span>
    <span>📅 <b>Daily Notes Link:</b> <code>.obsidian/daily-notes.json</code></span>
  </div>
</div>

<div class="dashboard-kpi-strip">
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Core Templates</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: var(--text-accent);">7 SCHEMAS</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Template Engine</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #4facfe;">OBSIDIAN CORE</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Daily Review Link</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #bb86fc;">AUTOMATED</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Layout Standard</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em;">RESPONSIVE CARDS</div>
  </div>
</div>

---

## 🧭 Template Quick Reference Matrix

| Template | File | Target Destination | Frontmatter `type` | Primary Persona / System |
|---|---|---|---|---|
| **[[#1. Project Dashboard\|Project Dashboard]]** | [`Project.md`](file:///_System/Templates/Project.md) | `01-Projects/` | `project` | Codex (Lead), Argus, Ledger, Vox |
| **[[#2. Architecture Decision Record (ADR)\|Architecture Decision Record]]** | [`Architecture-Decision-Record.md`](file:///_System/Templates/Architecture-Decision-Record.md) | `01-Projects/ADR/` | `adr` | 4-Agent Consensus Review |
| **[[#3. Lesson Learned\|Lesson Learned]]** | [`Lesson-Learned.md`](file:///_System/Templates/Lesson-Learned.md) | `02-Areas/Skills/Lessons-Learned/` | `lesson-learned` | Argus (Safety & Risk), Self-Correction |
| **[[#4. Daily Review\|Daily Review]]** | [`Daily-Review.md`](file:///_System/Templates/Daily-Review.md) | `04-Archives/Daily/YYYY/MM/` | `daily-review` | Daily Notes Plugin, Archiver Dataview |
| **[[#5. Research Note\|Research Note]]** | [`Research-Note.md`](file:///_System/Templates/Research-Note.md) | `03-Resources/Research/` | `research` | Deep Research, Literature & Tech Spikes |
| **[[#6. Personality Judgment Analysis\|Personality Judgment Analysis]]** | [`Personality-Judgment-Analysis.md`](file:///_System/Templates/Personality-Judgment-Analysis.md) | `02-Areas/` or `04-Archives/Daily/` | `analysis` | Vox (Human Alignment & Cognition) |
| **[[#7. Personality Judgment Dashboard\|Personality Judgment Dashboard]]** | [`Personality-Judgment-Dashboard.md`](file:///_System/Templates/Personality-Judgment-Dashboard.md) | `02-Areas/` or `04-Archives/Daily/` | Dynamic | Dataview & DataviewJS Telemetry |
| **[[#Bonus Memory Review Candidate\|Memory Review Candidate]]** | [`04-Archives/Memory-Review/TEMPLATE.md`](file:///04-Archives/Memory-Review/TEMPLATE.md) | `04-Archives/Memory-Review/` | Candidate | Memory Review Kanban Board |

---

## 📖 Comprehensive Template Specifications

### 1. Project Dashboard
- **File:** [`_System/Templates/Project.md`](file:///_System/Templates/Project.md)
- **Target Location:** `01-Projects/<Project-Name>.md`
- **When to Use:** Starting an active engineering initiative, complex agent workflow, or cross-tool integration with specific milestones, deliverables, and team assignments.
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
- **Structural Architecture:**
  - **Meta Banner:** Displays status badge, multi-agent squad pill, and repository/workspace paths.
  - **KPI Strip:** 4 status metrics (`Status`, `Priority`, `Lead Agent`, `Linked ADRs`).
  - **Column 1 (Strategy & Squad):** Goal & Executive Scope, Repository & Workspace Path, Architecture & Tech Stack, Multi-Agent Squad & Role Matrix (Codex, Argus, Ledger, Vox).
  - **Column 2 (Execution & Decisions):** Operational Stage, Action Checklist, Linked ADRs (`[[01-Projects/ADR/README|ADR Index]]`), and References.
- **Obsidian Placeholders:** `{{title}}`, `{{date}}`.

---

### 2. Architecture Decision Record (ADR)
- **File:** [`_System/Templates/Architecture-Decision-Record.md`](file:///_System/Templates/Architecture-Decision-Record.md)
- **Target Location:** `01-Projects/ADR/ADR-<Number>-<Title>.md`
- **When to Use:** Deciding significant technical, architectural, or structural changes that carry trade-offs or constraints.
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
- **Structural Architecture:**
  - **Context & Problem Statement:** What technical problem or question are we solving?
  - **Multi-Agent Persona Review:**
    - 🛡️ **Argus (Security & Risk):** Threat modeling, secret handling, attack surface.
    - ⚡ **Codex (Implementation & Performance):** Code complexity, maintainability, latency.
    - 📊 **Ledger (Resource Efficiency & Cost):** Token consumption, model inference costs, storage.
    - 🗣️ **Vox (Human Alignment & UX):** Developer ergonomics, communication clarity.
  - **Decision & Consensus:** Final chosen solution and rationale.
  - **Consequences:** Positive gains vs. accepted trade-offs.
  - **Footer:** Links to [[01-Projects/ADR/README|Architecture Decision Records Index]].

---

### 3. Lesson Learned
- **File:** [`_System/Templates/Lesson-Learned.md`](file:///_System/Templates/Lesson-Learned.md)
- **Target Location:** `02-Areas/Skills/Lessons-Learned/LL-<Topic>.md`
- **When to Use:** Post-incident review following an agent hallucination, API failure, tool misconfiguration, or bad assumption to prevent recurrence.
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
- **Structural Architecture:**
  - **Metadata Banner:** Incident date, agent profile, severity level.
  - **1. What Happened:** Trigger, prompt context, and erroneous action.
  - **2. Root Cause Analysis:** Why the mistake happened (outdated docs, hallucinated flags, path bugs).
  - **3. Human Correction & Fix:** How the issue was resolved.
  - **4. 🛡️ Standing Preventative Directive:** Strict, actionable directive the agent must adhere to in all future sessions.
  - **Footer:** Links to [[02-Areas/Skills/Lessons-Learned/README|Lessons Learned Catalog]].

---

### 4. Daily Review
- **File:** [`_System/Templates/Daily-Review.md`](file:///_System/Templates/Daily-Review.md)
- **Target Location:** `04-Archives/Daily/YYYY/MM/DD.md` (or `YYYY-MM-DD.md`)
- **When to Use:** Daily reflection and session triage. Automatically used by Obsidian's **Daily Notes** plugin.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: daily-review
  status: draft
  created: {{date}}
  tags: [daily-review]
  ---
  ```
- **Dynamic Dataview Integration:**
  Lists all Hermes chat session archives exported on this day from `04-Archives/Daily/YYYY/MM/DD/`:
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
- **Reflection Checklists:**
  - Sessions reviewed
  - Durable facts found (candidates for `04-Archives/Memory-Review/`)
  - Notes & follow-ups
  - Link to [[04-Archives/Memory-Review/TEMPLATE|Memory-Review Promotion Criteria]].

---

### 5. Research Note
- **File:** [`_System/Templates/Research-Note.md`](file:///_System/Templates/Research-Note.md)
- **Target Location:** `03-Resources/Research/<Topic>.md`
- **When to Use:** Deep dives into technical topics, libraries, prompt engineering patterns, security audits, or agent architectures.
- **YAML Frontmatter:**
  ```yaml
  ---
  type: research
  status: in-progress   # in-progress | complete | abandoned
  created: {{date}}
  tags: [research]
  ---
  ```
- **Structural Architecture:**
  - **Question / Goal:** The explicit question being investigated.
  - **Findings:** Key discoveries and takeaways.
  - **Sources:** Papers, GitHub repos, official docs, benchmarks.
  - **Open Threads:** Remaining unanswered questions.
  - **Related:** Reciprocal wikilinks to relevant vault notes and [[03-Resources/Research/README|Research Hub]].

---

### 6. Personality Judgment Analysis
- **File:** [`_System/Templates/Personality-Judgment-Analysis.md`](file:///_System/Templates/Personality-Judgment-Analysis.md)
- **Target Location:** `02-Areas/Skills/` or `04-Archives/Daily/`
- **When to Use:** In-depth cognitive, communicative, and psychological alignment analysis of conversational subjects or human-agent interaction patterns.
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
  1. Subject Profile (metadata, platform, data quality)
  2. Communication Style & shifts (formal, technical, defensive, casual, etc.)
  3. Language Pattern (vocabulary, sentence styles, grammatical voice)
  4. Repetition Analysis (event, complaint, justification, emotional functions)
  5. Response Behavior (work, conflict, casual, emotional)
  6. Conversation Dynamics (initiation, topic control, question behavior)
  7. Conflict & Disagreement (precursors, behaviors, repair mechanisms)
  8. Topic Behavior (message counts, latency, emotional variance)
  9. Baseline vs. Change (deviation from normal baseline)
  10. Anomaly Detection Log (tone, latency, volume anomalies)
  11. Context Node Summary (temporal, relational, developmental, environmental)
  12. Hypothesis Layer with Confidence Justification (High/Med/Low percentage rationale)
- **Framework Link:** [[02-Areas/Skills/Personality-Judgment-Framework|Personality Judgment Framework]].

---

### 7. Personality Judgment Dashboard
- **File:** [`_System/Templates/Personality-Judgment-Dashboard.md`](file:///_System/Templates/Personality-Judgment-Dashboard.md)
- **Target Location:** Dedicated hub note in `02-Areas/` or `04-Archives/`
- **When to Use:** Instantiating a real-time command center summarizing all active personality judgment analyses in the vault.
- **Key Widgets & DataviewJS:**
  - **Active Analyses Table:** Lists all subjects, styles, top hypotheses, and confidence.
  - **Confidence Distribution:** Dynamic DataviewJS counts of High, Medium, Low, and Very Low findings.
  - **Recent Hypotheses:** Flattened array query showing the latest 10 hypotheses.
  - **Timeline:** Historical chronology of evaluations.
  - **Topics Analyzed:** Aggregated frequency bar of recurring behavioral topics.
  - **Active Anomalies:** Surface flagged behavior spikes across all notes.

---

### Bonus: Memory Review Candidate Template
- **File:** [`04-Archives/Memory-Review/TEMPLATE.md`](file:///04-Archives/Memory-Review/TEMPLATE.md)
- **Target Location:** `04-Archives/Memory-Review/<Candidate-Topic>.md`
- **When to Use:** Staging a candidate fact extracted from a daily chat transcript before manually approving it into Hermes native `MEMORY.md` or `USER.md`.
- **4 Gatekeeper Criteria:**
  - Durable (matters in 6+ months)
  - Non-sensitive (zero API keys, credentials, or PII)
  - Verified (cited from session transcripts or repeatable observation)
  - Actionable (changes future agent behavior)
- **Verdict Checkbox:** Promote to memory · Promote to user profile · Archive.

---

## 🚀 How to Use Templates in Obsidian

### Method 1: Core Templates Plugin (`Ctrl+T` / `Cmd+T`)
1. Create a new note anywhere in your vault (`Ctrl+N` / `Cmd+N`).
2. Press `Ctrl+T` (Windows/Linux) or `Cmd+T` (macOS), or open the Command Palette (`Ctrl+P` / `Cmd+P`) and type `Insert template`.
3. Select any template from the list (e.g. `Project`, `Architecture-Decision-Record`, `Lesson-Learned`).
4. Obsidian will automatically populate the note and expand `{{date}}`, `{{time}}`, and `{{title}}`.

### Method 2: Daily Notes Button (One Click)
1. Click the **"Open today's daily note"** icon in Obsidian's left ribbon (or press your daily note shortcut).
2. Obsidian creates `04-Archives/Daily/YYYY/MM/DD.md` using [`Daily-Review.md`](file:///_System/Templates/Daily-Review.md).
3. The note immediately renders the live Dataview table of all chat sessions recorded today.

### Method 3: Via Hermes Agent Prompt
You can instruct your Hermes agent to create a note adhering to any template:
> *"Create a new Architecture Decision Record for our SQLite caching layer following `_System/Templates/Architecture-Decision-Record.md`. Include evaluations from Argus, Codex, Ledger, and Vox."*

---

*Catalog maintained in `_System/Templates/` — see [[_System/README|System Hub]] and [[MOC|Vault Map of Content]]*
