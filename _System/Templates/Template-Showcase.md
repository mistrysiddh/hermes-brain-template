---
type: index
status: active
tags:
  - system
  - templates
  - showcase
cssclasses:
  - dashboard-beta
  - dashboard-wide
---

# 📋 Templates Content Showcase & Raw Source Gallery

> [!TIP] How to View and Copy Templates
> In Obsidian, templates with complex Dataview queries or HTML containers often execute or format automatically. 
> This showcase displays the **verbatim raw markdown source code** for every template inside expandable code boxes. 
> Click **`Click to view & copy raw template markdown`**, then use Obsidian's top-right **Copy** button to copy the exact code in one click!

<div class="dashboard-kpi-strip">
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Total Templates</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: var(--text-accent);">8 SCHEMAS</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">View Mode</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #4facfe;">RAW SOURCE</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">1-Click Copy</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #bb86fc;">ENABLED</div>
  </div>
  <div class="dashboard-kpi-card">
    <div class="dashboard-kpi-label">Standard</div>
    <div class="dashboard-kpi-value" style="font-size: 1.25em;">PARA ALIGNED</div>
  </div>
</div>

---

## 🧭 Jump to Template

- **[[#1. Project Dashboard|1. Project Dashboard]]** (`Project.md`) — *Responsive 2-column project dashboard with KPI strip, executive goal, tech stack, multi-agent squad roles (Codex, Argus, Ledger, Vox), and action checklist*
- **[[#2. Architecture Decision Record (ADR)|2. Architecture Decision Record (ADR)]]** (`Architecture-Decision-Record.md`) — *Formal engineering decision record featuring 4-persona multi-agent review (Argus security, Codex technical, Ledger token efficiency, Vox alignment)*
- **[[#3. Lesson Learned|3. Lesson Learned]]** (`Lesson-Learned.md`) — *Self-correction template capturing triggers, root cause analysis, human corrections, and standing preventative directives to prevent recurring agent mistakes*
- **[[#4. Daily Review|4. Daily Review]]** (`Daily-Review.md`) — *Daily reflection schema configured with Obsidian Daily Notes plugin*
- **[[#5. Research Note|5. Research Note]]** (`Research-Note.md`) — *Structured research investigation brief with explicit sections for research question/goal, empirical findings, cited sources, and open inquiry threads*
- **[[#6. Personality Judgment Analysis|6. Personality Judgment Analysis]]** (`Personality-Judgment-Analysis.md`) — *Deep 7-dimension behavioral and communication evaluation analyzing baseline communication, cognitive style, collaboration, tone, and behavioral anomalies*
- **[[#7. Personality Judgment Dashboard|7. Personality Judgment Dashboard]]** (`Personality-Judgment-Dashboard.md`) — *Dataview and DataviewJS telemetry dashboard aggregating cross-session analyses, confidence levels, anomalies, and active behavioral hypotheses*
- **[[#8. Memory Review Candidate|8. Memory Review Candidate]]** (`TEMPLATE.md`) — *Memory promotion rubric enforcing durability, security, and verification gates before facts are promoted into long-term agent memory or user profile*

---

### 1. Project Dashboard

> **File:** [`Project.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/_System/Templates/Project.md) | **Target:** `01-Projects/<Project-Name>.md` | **Insert:** `Ctrl+T → Select 'Project'`

*Responsive 2-column project dashboard with KPI strip, executive goal, tech stack, multi-agent squad roles (Codex, Argus, Ledger, Vox), and action checklist.*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> ---
> type: project
> status: active
> created: {{date}}
> tags:
>   - project
> cssclasses:
>   - dashboard-beta
>   - dashboard-wide
> ---
>
> # 🚀 {{title}}
>
> <div class="project-meta-banner">
>   <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
>     <span class="dashboard-badge dashboard-badge-ok">🟢 Active Project</span>
>     <span class="dashboard-badge dashboard-badge-purple">📁 Project Workspace</span>
>     <span class="dashboard-badge dashboard-badge-blue">🤖 Multi-Agent Squad</span>
>   </div>
>   <div style="display: flex; align-items: center; gap: 12px; font-size: 0.85em; color: var(--text-muted);">
>     <span>📅 <b>Created:</b> {{date}}</span>
>     <span>📍 <b>Repo / Path:</b> <code>path/to/repo</code></span>
>   </div>
> </div>
>
> <div class="dashboard-kpi-strip">
>   <div class="dashboard-kpi-card">
>     <div class="dashboard-kpi-label">Status</div>
>     <div class="dashboard-kpi-value" style="font-size: 1.25em; color: var(--text-accent);">ACTIVE</div>
>   </div>
>   <div class="dashboard-kpi-card">
>     <div class="dashboard-kpi-label">Priority</div>
>     <div class="dashboard-kpi-value" style="font-size: 1.25em;">HIGH</div>
>   </div>
>   <div class="dashboard-kpi-card">
>     <div class="dashboard-kpi-label">Lead Agent</div>
>     <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #4facfe;">CODEX</div>
>   </div>
>   <div class="dashboard-kpi-card">
>     <div class="dashboard-kpi-label">Linked ADRs</div>
>     <div class="dashboard-kpi-value" style="font-size: 1.25em; color: #bb86fc;">0</div>
>   </div>
> </div>
>
> <div class="project-2col">
>
> <div class="project-col">
>
> <div class="dashboard-card">
>
> ### 🎯 Goal & Executive Scope
>
> - **Objective:** What is the primary objective and mission of this project?
> - **User Impact:** What problem does this solve for the user or agent workflow?
> - **Success Criteria:** How will we evaluate when this project is completed or production-ready?
>
> </div>
>
> <div class="dashboard-card">
>
> ### 📦 Repository & Workspace Path
>
> - **Repository:** `https://github.com/username/repo-name`
> - **Local Workspace:** `C:\path\to\workspace`
> - **Target Branch / Environment:** `main` / `production`
>
> </div>
>
> <div class="dashboard-card">
>
> ### 🏗️ Architecture & Specifications
>
> - **Key Components:**
>   - Component 1
>   - Component 2
> - **Tech Stack & Dependencies:**
>   - Python / TypeScript / Node.js
>   - SQLite / Postgres / JSON storage
>
> </div>
>
> <div class="dashboard-card">
>
> ### 🤖 Multi-Agent Squad & Roles
>
> - **⚡ Codex:** Lead developer, coding, tests, and refactors.
> - **🛡️ Argus:** Security, credentials protection, and vulnerability review.
> - **📊 Ledger:** Token budget, cost analysis, and computational efficiency.
> - **🗣️ Vox:** Documentation, human feedback alignment, and prompt styling.
>
> </div>
>
> </div>
>
> <div class="project-col">
>
> <div class="dashboard-card">
>
> ### ⚡ Current Operational Status
>
> - **Current Stage:** Exploration / Implementation / Testing / Deployment
> - **Active Sprint / Milestone:** Milestone 1
> - **Blockers / Key Risks:** None currently identified.
>
> </div>
>
> <div class="dashboard-card">
>
> ### ✅ Next Actions & Milestones
>
> - [ ] Initialize repository structure and environment
> - [ ] Define core architectural boundaries and interfaces
> - [ ] Implement initial prototype and feature logic
> - [ ] Perform security and secret scrubbing review
> - [ ] Conduct multi-agent performance and token evaluation
> - [ ] Ship release and document operational instructions
>
> </div>
>
> <div class="dashboard-card">
>
> ### 📑 Durable Decisions & ADRs
>
> - [[01-Projects/ADR/README|ADR Index]]
> - Record architectural invariants, non-negotiable requirements, or data schemas here.
>
> </div>
>
> <div class="dashboard-card">
>
> ### 📚 Sources, Documentation & Quick Links
>
> - Relevant docs, PRs, research notes, or reference links go here.
> - See also: [[01-Projects/README|All Projects]] · [[Dashboard|Vault Dashboard]]
>
> </div>
>
> </div>
>
> </div>
> ````

---

### 2. Architecture Decision Record (ADR)

> **File:** [`Architecture-Decision-Record.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/_System/Templates/Architecture-Decision-Record.md) | **Target:** `01-Projects/ADR/ADR-<Number>-<Title>.md` | **Insert:** `Ctrl+T → Select 'Architecture-Decision-Record'`

*Formal engineering decision record featuring 4-persona multi-agent review (Argus security, Codex technical, Ledger token efficiency, Vox alignment).*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> ---
> type: adr
> status: proposed # proposed | accepted | rejected | superseded
> date: {{date}}
> deciders: [Human, Codex, Argus, Ledger, Vox]
> tags: [adr, architecture, multi-agent]
> ---
>
> # 📑 ADR-{{title}}
>
> > **Status:** `proposed` | **Date:** {{date}} | **Deciders:** `[Human, Codex, Argus, Ledger, Vox]`
>
> ## 1. Context & Problem Statement
> * What technical decision or architecture question are we solving?
> * What constraints, trade-offs, or requirements must be considered?
>
> ## 2. Multi-Agent Persona Review
>
> ### 🛡️ Argus (Security & Risk)
> * Threat modeling, credential exposure, attack surface, and security boundaries:
>   > 
>
> ### ⚡ Codex (Implementation & Performance)
> * Technical architecture, code complexity, maintainability, and latency/speed:
>   > 
>
> ### 📊 Ledger (Resource Efficiency & Cost)
> * Token consumption, model inference costs, data retention, and storage overhead:
>   > 
>
> ### 🗣️ Vox (Human Alignment & UX)
> * Communication clarity, developer experience, cognitive ergonomics, and readability:
>   > 
>
> ## 3. Decision & Consensus
> * **Chosen Architecture:**
>   > 
> * **Consensus Rationale:**
>   * 
>
> ## 4. Consequences
> * **Positive Impact:**
>   * 
> * **Negative / Trade-off Acceptance:**
>   * 
>
> ---
> *Maintained in [[01-Projects/ADR/README|Architecture Decision Records]]*
> ````

---

### 3. Lesson Learned

> **File:** [`Lesson-Learned.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/_System/Templates/Lesson-Learned.md) | **Target:** `02-Areas/Skills/Lessons-Learned/<Topic>.md` | **Insert:** `Ctrl+T → Select 'Lesson-Learned'`

*Self-correction template capturing triggers, root cause analysis, human corrections, and standing preventative directives to prevent recurring agent mistakes.*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> ---
> type: lesson-learned
> date: {{date}}
> agent_profile: default
> status: active
> severity: low # low | medium | high
> tags: [lesson-learned, self-correction, hermes-brain]
> ---
>
> # ⚠️ Lesson Learned: {{title}}
>
> > **Incident Date:** {{date}} | **Agent Profile:** `default` | **Severity:** `low`
>
> ## 1. What Happened (Trigger & Action)
> * **User Prompt / Intent:**
>   > 
> * **Agent Erroneous Action:**
>   > 
>
> ## 2. Root Cause Analysis
> * **Why did the failure occur?** (e.g. bad assumption, outdated documentation, hallucinated CLI flag, path misconfiguration)
>   * 
>
> ## 3. Human Correction & Fix
> * **How was the issue resolved?**
>   * 
>
> ## 4. 🛡️ Standing Preventative Directive
> * **Rule to adhere to in all future sessions:**
>   > 
>
> ---
> *Maintained in [[02-Areas/Skills/Lessons-Learned/README|Lessons Learned Catalog]] to prevent recurrent mistakes.*
> ````

---

### 4. Daily Review

> **File:** [`Daily-Review.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/_System/Templates/Daily-Review.md) | **Target:** `04-Archives/Daily/YYYY/MM/YYYY-MM-DD-Review.md` | **Insert:** `Alt+D (or ribbon Daily Note icon)`

*Daily reflection schema configured with Obsidian Daily Notes plugin. Includes automated Dataview query auditing all chat sessions archived during that day.*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> ---
> type: daily-review
> status: draft
> created: {{date}}
> tags: [daily-review]
> ---
>
> # Daily Review — {{date}}
>
> ## 💬 Sessions for this day
>
> ```dataview
> TABLE file.mtime AS "Modified", file.size AS "Size"
> FROM "04-Archives/Daily" OR "Daily"
> WHERE (file.folder = this.file.folder + "/" + this.file.name OR file.folder = this.file.folder) AND file.name != this.file.name AND file.name != "README" AND file.name != "manifest" AND !contains(file.tags, "daily-review")
> SORT file.name ASC
> ```
>
> ## Sessions reviewed
> - 
>
>
> ## Durable facts found
> - [ ] 
>
> ## Flagged for Memory-Review
> - 
>
> ## Notes / follow-ups
> - 
>
> ---
> See [[04-Archives/Memory-Review/TEMPLATE|Memory-Review promotion criteria]] before staging anything as a candidate.
> ````

---

### 5. Research Note

> **File:** [`Research-Note.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/_System/Templates/Research-Note.md) | **Target:** `03-Resources/Research/<Topic>.md` | **Insert:** `Ctrl+T → Select 'Research-Note'`

*Structured research investigation brief with explicit sections for research question/goal, empirical findings, cited sources, and open inquiry threads.*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> ---
> type: research
> status: in-progress
> created: {{date}}
> tags: [research]
> ---
>
> # {{title}}
>
> ## Question / goal
>
>
> ## Findings
> - 
>
> ## Sources
> - 
>
> ## Open threads
> - 
>
> ## Related
> - 
>
> ---
> *Maintained in [[03-Resources/Research/README|Research Hub]] · [[Dashboard|Dashboard]]*
> ````

---

### 6. Personality Judgment Analysis

> **File:** [`Personality-Judgment-Analysis.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/_System/Templates/Personality-Judgment-Analysis.md) | **Target:** `02-Areas/ or 04-Archives/Daily/YYYY/MM/DD/` | **Insert:** `Ctrl+T → Select 'Personality-Judgment-Analysis'`

*Deep 7-dimension behavioral and communication evaluation analyzing baseline communication, cognitive style, collaboration, tone, and behavioral anomalies.*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> ---
> type: analysis
> status: active
> created: {{date}}
> tags: [analysis, personality-judgment]
> subject: ""
> period: ""
> primary_style: ""
> top_hypothesis: ""
> confidence: ""
> hypotheses: []
> anomalies: []
> recommendations: []
> topic_behavior: []
> ---
>
> # Personality Judgment Analysis Template
>
> Use this template to conduct a structured personality judgment analysis following the framework in [[02-Areas/Skills/Personality-Judgment-Framework|Personality Judgment Framework]].
>
> ## 📋 Instructions
> 1. Duplicate this template for each new analysis
> 2. Fill in all sections based on your observations
> 3. Link to relevant session exports, skill usage data, or other vault notes
> 4. Update confidence levels as new evidence arrives
> 5. Consider linking to related analyses or MOCs as appropriate
>
> ## 📊 Analysis Metadata (for dashboard tracking)
> - **subject**:: [Subject ID/name]
> - **period**:: [Analysis period]
> - **primary_style**:: [Primary Style Observed]
> - **top_hypothesis**:: [Brief title of highest confidence hypothesis]
> - **confidence**:: [Confidence level of top hypothesis: High/Medium/Low/Very Low]
> - **hypotheses**:: [List of hypothesis titles]
> - **anomalies**:: [List of anomaly dimensions observed]
> - **recommendations**:: [List of key recommendations]
> - **topic_behavior**:: [List of topics analyzed in Topic Behavior section]
>
> ---
>
> ## 1. Subject Profile
>
> | Element | Description | Your Analysis |
> |---------|-------------|---------------|
> | **Subject ID/name** | Unique identifier |  |
> | **Analysis period** | Timeframe covered |  |
> | **Platform** | Communication medium |  |
> | **Number of messages** | Total communications analyzed |  |
> | **Number of conversations** | Distinct interaction threads |  |
> | **Participants** | Other parties involved |  |
> | **Data quality** | Reliability assessment |  |
> | **Missing periods** | Gaps in data |  |
> | **Context** | Relevant background |  |
>
> > 💡 **Tip**: Be specific about dates, platforms, and data sources. Note any limitations upfront.
>
> ---
>
> ## 2. Communication Style
>
> ### Primary Style Observed: [e.g., Casual, Technical, Friendly]
>
> ### Style Distribution (estimate %):
> - Formal: ____%
> - Casual: ____%
> - Friendly: ____%
> - Neutral: ____%
> - Assertive: ____%
> - Defensive: ____%
> - Sarcastic: ____%
> - Humorous: ____%
> - Emotional: ____%
> - Technical: ____%
> - Reserved: ____%
>
> ### Style Shifts Noted:
> - [Describe any significant changes in style across contexts, topics, or time]
> - Example: "Shifted from Formal to Casual after establishing rapport in conversation #3"
>
> ---
>
> ## 3. Language Pattern
>
> ### Vocabulary Analysis
> | Category | Examples Observed | Frequency/Notes |
> |----------|-------------------|-----------------|
> | **Frequently used words** |  |  |
> | **Rare words** |  |  |
> | **Slang** |  |  |
> | **Technical terms** |  |  |
> | **Filler words** |  |  |
> | **Profanity** |  |  |
> | **Formal vocabulary** |  |  |
>
> ### Sentence Style Analysis
> | Type | Count/Examples | Notes |
> |------|----------------|-------|
> | **Short** (<10 words) |  |  |
> | **Medium** (10-20 words) |  |  |
> | **Long** (>20 words) |  |  |
> | **Questions** |  |  |
> | **Commands** |  |  |
> | **Statements** |  |  |
> | **Explanations** |  |  |
> | **Storytelling** |  |  |
>
> ### Grammar Patterns
> | Feature | Observed Usage | Significance Notes |
> |---------|----------------|-------------------|
> | **First-person usage** |  |  |
> | **Second-person usage** |  |  |
> | **Passive voice** |  |  |
> | **Active voice** |  |  |
> | **Hedging** |  |  |
>
> ---
>
> ## 4. Repetition Analysis
>
> | Repetition Type | Examples Observed | Possible Function |
> |-----------------|-------------------|-------------------|
> | **Event repetition** |  |  |
> | **Complaint repetition** |  |  |
> | **Explanation repetition** |  |  |
> | **Person repetition** |  |  |
> | **Topic repetition** |  |  |
> | **Justification repetition** |  |  |
>
> > 🔍 **Key insight**: What need does this repetition serve? (Validation? Control? Connection? Anxiety reduction?)
>
> ---
>
> ## 5. Response Behavior
>
> ### Primary Response Categories (estimate %):
> - Work: ____%
> - Technical: ____%
> - Casual: ____%
> - Conflict: ____%
> - Personal: ____%
>
> ### Category Examples:
> - **Work**: [Examples of task-oriented responses]
> - **Technical**: [Examples of specification/detail-focused responses]
> - **Casual**: [Examples of social/relationship-focused responses]
> - **Conflict**: [Examples of disagreement/opposition-focused responses]
> - **Personal**: [Examples of self-disclosure/feeling-focused responses]
>
> ---
>
> ## 6. Conversation Dynamics
>
> ### Initiation Patterns
> - **Who starts conversations**: [Percentage by each party]
> - **How often**: [Frequency per time unit]
> - **What topics initiated**: [Subject matter of opening messages]
>
> ### Topic Control
> - **Topic introducer**: [Who brings up new subjects most often]
> - **Topic changer**: [Who redirects conversation most frequently]
> - **Conversation ender**: [Who concludes interactions most often]
>
> ### Question Behavior
> | Type | Count/Examples | Notes |
> |------|----------------|-------|
> | **Questions asked** |  |  |
> | **Questions answered** |  |  |
> | **Questions ignored** |  |  |
> | **Questions redirected** |  |  |
>
> ---
>
> ## 7. Conflict & Disagreement Analysis
>
> If applicable, document any conflict episodes:
>
> ### Conflict Episode #1: [Brief description or timestamp]
>
> #### Before Conflict →
> - **Observable precursors**: 
> - **Contextual factors**: 
>
> #### During Conflict →
> | Behavior | Observed (Y/N) | Examples/Notes |
> |----------|----------------|----------------|
> | Defensiveness |  |  |
> | Explanation |  |  |
> | Counterargument |  |  |
> | Topic shifting |  |  |
> | Silence |  |  |
> | Repetition |  |  |
> | Apology |  |  |
> | Negotiation |  |  |
> | Escalation |  |  |
> | Conversation termination |  |  |
>
> #### After Conflict →
> - **Repair behaviors**: 
> - **Avoidance patterns**: 
> - **Learning integration**: 
>
> > 🔄 **Repeat for additional conflict episodes as needed**
>
> ---
>
> ## 8. Topic Behavior Analysis
>
> For each significant topic, complete:
>
> ### Topic: [Name of topic]
>
> | Metric | Measurement | Notes |
> |--------|-------------|-------|
> | **Frequency** |  |  |
> | **Message count** |  |  |
> | **Average length** |  |  |
> | **Response time** |  |  |
> | **Emotional language** |  |  |
> | **Topic initiation** |  |  |
> | **Topic avoidance/change** |  |  |
> | **Recurrence** |  |  |
>
> > 📊 **Repeat for additional topics as needed**
>
> ---
>
> ## 9. Baseline vs. Change Analysis
>
> ### Established Baseline (Normal Behavior):
> - **Communication style**: 
> - **Typical initiation patterns**: 
> - **Usual topic preferences**: 
> - **Standard response timing**: 
> - **Baseline emotional expression**: 
>
> ### Detected Changes From Normal:
> - **Style shifts**: 
> - **Topic anomalies**: 
> - **Timing alterations**: 
> - **Style deviations**: 
> - **Volume changes**: 
> - **Other changes**: 
>
> > 🔑 **Key insight**: What do these changes suggest about internal state, external stressors, or relationship evolution?
>
> ---
>
> ## 10. Anomaly Detection Log
>
> Significant deviations observed:
>
> | Dimension | Anomaly Observed | Context | Possible Significance |
> |-----------|------------------|---------|----------------------|
> | **Tone** |  |  |  |
> | **Vocabulary** |  |  |  |
> | **Message length** |  |  |  |
> | **Response time** |  |  |  |
> | **Emoji use** |  |  |  |
> | **Topic focus** |  |  |  |
> | **Question frequency** |  |  |  |
> | **Conversation initiation** |  |  |  |
> | **Activity hours** |  |  |  |
> | **Formality** |  |  |  |
> | **Repetition patterns** |  |  |  |
>
> > 🚨 **Alert protocol**: Flag anomalies lasting >3 conversations or in high-stakes contexts.
>
> ---
>
> ## 11. Context Node Summary
>
> Key contextual factors influencing the analysis:
> - **Temporal**: [Time of day, day of week, recent events]
> - **Relational**: [Who present, relationship history, power dynamics]
> - **Environmental**: [Physical setting, stressors, distractions]
> - **Developmental**: [Life stage, skill acquisition, healing processes]
> - **Cultural**: [Norms, expectations, communication scripts]
> - **Situational**: [Specific goals, pressures, opportunities]
>
> > 🌐 **Remember**: The same behavior means different things in different contexts.
>
> ---
>
> ## 12. Hypothesis Layer
>
> For each significant pattern observed, complete this template:
>
> ### Hypothesis #1: [Brief title]
>
> #### Observation
> > "Raw message excerpt showing [specific behavior]"
>
> #### Observable Feature
> > "Measurable characteristic: [e.g., response time increased from 8 minutes to 74 minutes]"
>
> #### Pattern
> > "Recurrence across instances: [e.g., This occurred in 8 of 10 conversations involving topic X]"
>
> #### Context
> > "Situational factors: [e.g., Occurred during after-hours technical discussions when subject reported fatigue]"
>
> #### Hypothesis
> > "Tentative explanation: [e.g., Subject avoids deep technical engagement when tired due to fear of making mistakes]"
>
> #### Confidence Level (with justification)
> > **[High/Medium/Low/Very Low]** (XX-XX%): [Justification based on evidence strength, number of examples, ruled out alternatives]
>
> > *Confidence justification*: [e.g., "Medium: Pattern observed in 8/10 relevant conversations but alternative explanation (topic difficulty) not fully ruled out"]
>
> #### Evidence
> > **Supporting**: [Specific examples confirming hypothesis]
> > **Contradicting**: [Specific examples challenging hypothesis]
> > **Neutral**: [Observations neither confirming nor denying]
>
> > 💡 **Repeat for additional hypotheses as needed**
>
> ---
>
> ## 📌 Analysis Summary & Conclusions
>
> ### Key Patterns Identified:
> 1. 
> 2. 
> 3. 
>
> ### Primary Hypotheses (with confidence):
> 1. [Hypothesis] - [Confidence]%
> 2. [Hypothesis] - [Confidence]%
> 3. [Hypothesis] - [Confidence]%
>
> ### Recommended Actions or Next Steps:
> 1. 
> 2. 
> 3. 
>
> ### Limitations of This Analysis:
> - 
> - 
> - 
>
> ### Linked Resources:
> - [[04-Archives/Daily/README|04-Archives/Daily/YYYY/MM/DD/]] - Session exports
> - [[02-Areas/Skills/Skill-to-Chat-Links|Skill-to-Chat-Links]] - Skill usage data
> - [[04-Archives/Memory-Review/README|04-Archives/Memory-Review/]] - Promoted durable knowledge
> - [[MOC|Map of Content (MOC)]] - High-level navigation hub
>
> ---
> *Analysis conducted using Personality Judgment Framework v1.0 | Completed: {{date}} | Next review suggested: 7 days from completion*
> ````

---

### 7. Personality Judgment Dashboard

> **File:** [`Personality-Judgment-Dashboard.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/_System/Templates/Personality-Judgment-Dashboard.md) | **Target:** `02-Areas/ or 04-Archives/Daily/YYYY/MM/DD/` | **Insert:** `Ctrl+T → Select 'Personality-Judgment-Dashboard'`

*Dataview and DataviewJS telemetry dashboard aggregating cross-session analyses, confidence levels, anomalies, and active behavioral hypotheses.*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> # Personality Judgment Dashboard
>
> A dynamic Dataview-powered dashboard for tracking and visualizing personality judgment analyses.
>
> ## 📊 Active Analyses
>
> ```dataview
> TABLE
>   subject AS "Subject",
>   period AS "Period",
>   primary_style AS "Primary Style",
>   top_hypothesis AS "Top Hypothesis",
>   confidence AS "Confidence",
>   dateformat(file.mtime, "yyyy-MM-dd") AS "Updated"
> FROM #personality-judgment or "04-Archives/Daily" or "02-Areas" or "03-Resources"
> WHERE subject AND !contains(file.folder, "_System/Templates") AND file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md"
> SORT file.mtime DESC
> ```
>
> ## 📈 Confidence Distribution
>
> ```dataviewjs
> const pages = dv.pages('#personality-judgment or "04-Archives/Daily" or "02-Areas" or "03-Resources"')
>   .where(p => !p.file.folder.includes("_System/Templates") && p.file.name !== "Personality-Judgment-Analysis.md" && p.file.name !== "Personality-Judgment-Dashboard.md" && p.subject);
>
> const confidenceCounts = {
>   High: 0,
>   Medium: 0,
>   Low: 0,
>   "Very Low": 0
> };
>
> for (const p of pages) {
>   const conf = p.confidence ? p.confidence.toString().trim() : "Unknown";
>   if (confidenceCounts[conf] !== undefined) {
>     confidenceCounts[conf]++;
>   }
> }
>
> dv.table(["Confidence Level", "Count"],
>   Object.entries(confidenceCounts).filter(([_, count]) => count > 0)
>     .map(([level, count]) => [level, count])
> );
> ```
>
> ## 🔍 Recent Hypotheses
>
> ```dataview
> TABLE
>   hypothesis AS "Hypothesis",
>   subject AS "Subject",
>   confidence AS "Confidence"
> FROM #personality-judgment or "04-Archives/Daily" or "02-Areas" or "03-Resources"
> WHERE !contains(file.folder, "_System/Templates") AND file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md" AND hypotheses
> FLATTEN hypotheses AS hypothesis
> WHERE hypothesis
> SORT file.mtime DESC
> LIMIT 10
> ```
>
> ## 📅 Analysis Timeline
>
> ```dataview
> TABLE WITHOUT ID
>   dateformat(file.mtime, "yyyy-MM-dd") AS "Date",
>   file.link AS "Analysis",
>   subject AS "Subject",
>   primary_style AS "Style",
>   confidence AS "Confidence"
> FROM #personality-judgment or "04-Archives/Daily" or "02-Areas" or "03-Resources"
> WHERE subject AND !contains(file.folder, "_System/Templates") AND file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md"
> SORT file.mtime DESC
> ```
>
> ## 🏷️ Topics Analyzed
>
> ```dataviewjs
> const pages = dv.pages('#personality-judgment or "04-Archives/Daily" or "02-Areas" or "03-Resources"')
>   .where(p => !p.file.folder.includes("_System/Templates") && p.file.name !== "Personality-Judgment-Analysis.md" && p.file.name !== "Personality-Judgment-Dashboard.md" && p.topic_behavior);
>
> const topicCounts = {};
>
> for (const p of pages) {
>   if (p.topic_behavior) {
>     const topics = Array.isArray(p.topic_behavior) ? p.topic_behavior : [p.topic_behavior];
>     for (const topic of topics) {
>       topicCounts[topic] = (topicCounts[topic] || 0) + 1;
>     }
>   }
> }
>
> const sortedTopics = Object.entries(topicCounts)
>   .sort((a, b) => b[1] - a[1])
>   .slice(0, 10);
>
> dv.table(["Topic", "Analyses Count"], sortedTopics);
> ```
>
> ## ⚠️ Active Anomalies
>
> ```dataview
> TABLE
>   anomaly AS "Anomaly",
>   subject AS "Subject",
>   file.link AS "Analysis"
> FROM #personality-judgment or "04-Archives/Daily" or "02-Areas" or "03-Resources"
> WHERE !contains(file.folder, "_System/Templates") AND file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md" AND anomalies
> FLATTEN anomalies AS anomaly
> WHERE anomaly
> SORT file.mtime DESC
> ```
>
> ## 💡 Recommendations Summary
>
> ```dataview
> LIST
>   recommendation
> FROM #personality-judgment or "04-Archives/Daily" or "02-Areas" or "03-Resources"
> WHERE !contains(file.folder, "_System/Templates") AND file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md" AND recommendations
> FLATTEN recommendations AS recommendation
> WHERE recommendation
> LIMIT 20
> ```
>
> ---
> *Dashboard updates automatically as you create and update personality judgment analyses*
> *Last updated: {{date}}*
> ````

---

### 8. Memory Review Candidate

> **File:** [`TEMPLATE.md`](file:///C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Hermes-Brain-Template/04-Archives/Memory-Review/TEMPLATE.md) | **Target:** `04-Archives/Memory-Review/<Candidate-Name>.md` | **Insert:** `Manual duplicate / Kanban card creation`

*Memory promotion rubric enforcing durability, security, and verification gates before facts are promoted into long-term agent memory or user profile.*

> [!example]- 📋 Click to view & copy raw template markdown
> ````markdown
> # Memory Review Template
>
> Use this before promoting any candidate fact to Hermes's native MEMORY.md/USER.md.
>
> **Where candidates come from**: pull them out of raw chat records in [[04-Archives/Daily/README|04-Archives/Daily/YYYY/MM/DD/]], from active research in [[03-Resources/Research/README|03-Resources/Research/]], or from [[Supermemory-All-Memory-Entries]] (auto-extracted Supermemory memory chunks, if you use Supermemory). **Where they attribute to**: if more than one agent works in this vault, check [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] for which one observed/produced the fact — record it in "Source/Session" below (a single-agent setup can skip this). Project context: [[01-Projects/Hermes-Agent-Vault-Setup|Hermes-Agent-Vault-Setup]].
>
> | Criterion | Required? | Notes |
> |-----------|-----------|-------|
> | Durable (matters in 6+ months) | Yes | Not task-specific |
> | Non-sensitive | Yes | No secrets, PII, client data |
> | Verified | Yes | Source cited or observed repeatedly |
> | Actionable | Preferred | Changes agent behavior |
>
> ## Candidate
> - Fact:
> - Source/Session:
> - Date observed:
>
> ## Verdict
> - [ ] Promote to memory
> - [ ] Promote to user profile
> - [ ] Archive (not durable / not verified)
> ````

---

## 🛠️ How to Add or Modify Templates

1. Create or edit any `.md` file inside [`_System/Templates/`](file:///_System/Templates/).
2. Keep frontmatter clean with `type: <category>`, `created: {{date}}`, and relevant tags.
3. Run `python _System/Scripts/generate_template_showcase.py` to re-sync this showcase file automatically.

---
*Reference documentation: [[_System/Templates/README|Templates Reference Catalog]] · [[Dashboard|Vault Dashboard]]*
