---
type: templates-review
status: active
created: 2026-09-22
tags: [templates, system, review, dataview]
---

# 📋 Templates Review — 2026-09-22

Central audit and review note for all note templates in this vault, formatted in the Daily-Review style with live Dataview queries.

## 📝 Registered Templates in this Vault

```dataview
TABLE
  type AS "Frontmatter Type",
  status AS "Default Status",
  choice(length(tags) > 0, tags, "none") AS "Tags",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") AS "Last Modified"
FROM "_System/Templates"
WHERE file.name != "README" AND file.name != "Template-Showcase" AND file.name != this.file.name
SORT file.name ASC
```

## 🔍 Templates Reviewed
- [x] [[_System/Templates/Project|Project.md]] — Widescreen 2-column active project charter & multi-agent squad matrix (Codex, Argus, Ledger, Vox).
- [x] [[_System/Templates/Architecture-Decision-Record|Architecture-Decision-Record.md]] — Formal 4-agent consensus decision record with security, code, cost, and UX reviews.
- [x] [[_System/Templates/Lesson-Learned|Lesson-Learned.md]] — Operational post-mortem with root-cause analysis, human corrections, and standing preventative directives.
- [x] [[_System/Templates/Daily-Review|Daily-Review.md]] — Evening reflection and automated Dataview chat session audit for the day.
- [x] [[_System/Templates/Research-Note.md|Research-Note.md]] — Structured technical inquiry brief with empirical findings, sources, and open threads.
- [x] [[_System/Templates/Personality-Judgment-Analysis|Personality-Judgment-Analysis.md]] — 7-dimension cognitive evaluation analyzing communication, tone, and behavioral anomalies.
- [x] [[_System/Templates/Personality-Judgment-Dashboard|Personality-Judgment-Dashboard.md]] — Dataview and DataviewJS telemetry tracker aggregating cross-session analyses.
- [x] [[04-Archives/Memory-Review/TEMPLATE|Memory Review Template]] — Gatekeeper criteria (durable, non-sensitive, verified, actionable) before fact promotion.

## 🛡️ Durable Schema Standards Found
- [x] **Obsidian Core Compatibility:** All templates rely strictly on native `{{title}}` and `{{date}}` variables.
- [x] **Clean Frontmatter:** Every template has valid YAML frontmatter specifying `type:`, `status:`, and `tags:`.
- [x] **PARA Path Compliance:** All wikilinks navigate cleanly across `01-Projects/`, `02-Areas/`, `03-Resources/`, and `04-Archives/`.
- [x] **No Execution Errors:** Dataview queries exclude template definition folders to prevent self-referential query errors.

## 📌 Flagged for Customization & Agent Alignment
- [ ] Customize lead agent personas in `Project.md` if using specialized models or single-agent workflows.
- [ ] Set your preferred severity defaults in `Lesson-Learned.md`.
- [ ] Ensure Dataview plugin is toggled ON in **Settings → Community plugins**.

## 💡 Notes & Follow-ups
- **Insertion Shortcut:** Use `Ctrl+T` (or `Cmd+T` on macOS) in any empty note to insert a template.
- **Daily Review Shortcut:** Press `Alt+D` (or click the ribbon calendar icon) to generate today's Daily Review.
- **Raw Code Copying:** To view or copy the exact unrendered source code of any template, open [[_System/Templates/Template-Showcase|Template-Showcase.md]].

---
*Maintained in [[_System/Templates/README|Templates Catalog]] · [[_System/Templates/Template-Showcase|Template Showcase]] · [[Dashboard|Vault Dashboard]]*
