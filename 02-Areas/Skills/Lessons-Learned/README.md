---
type: index
status: active
tags: [lessons-learned, index, self-correction]
---

# ⚠️ Agent Lessons Learned & Self-Correction Catalog

This directory catalogs agent operational failures, edge-case misunderstandings, and their permanent corrective directives.

> [!TIP]
> When the agent makes a mistake, instantiate a note here using `_System/Templates/Lesson-Learned.md`. The standing directive will be indexed here to ensure the agent never repeats the same error.

## Active Preventative Directives

```dataview
TABLE date as "Date", severity as "Severity", agent_profile as "Agent"
FROM "02-Areas/Skills/Lessons-Learned" or "Skills-Notes/Lessons-Learned"
WHERE file.name != "README"
SORT date desc
```

## Cross-links
- [[02-Areas/User-Profile|User Profile (Standing Rules)]]
- [[_System/Canvases/Dashboard-Beta|Executive Dashboard]]
- [[02-Areas/Skills/Team-Profiles-Index|Multi-Agent Team Profiles]]
