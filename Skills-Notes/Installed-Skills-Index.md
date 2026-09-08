---
type: reference
status: template
created: 2026-09-08
tags: [skills, reference]
---

# Installed Skills Index

Every Hermes skill installed for this vault's agent(s) — name + one-line
description. This ships as an empty starter table on purpose: your real
skill list is specific to your Hermes install, so the template doesn't
commit one.

There's no script that auto-populates this table (skill installation isn't
something this repo can introspect) — hand-maintain it, or regenerate it
from `hermes skills list` (or your Hermes install's equivalent) whenever
your installed set changes. This is different from
[[Skill-to-Chat-Links]], which *is* auto-generated (from `Daily/`, by
`Scripts/generate_skill_links.py`) — that one tells you which skills were
actually *used*, this one tells you which skills are *available*.

| Skill | Description |
|---|---|
| | |

## Cross-links
- [[Team-Profiles-Index]] — which profile tends to reach for which skill
- [[Skill-to-Chat-Links]] — which archived sessions actually invoked each skill
- [[../Daily/Chat-Correlation]] — live session breakdown by source/profile
