---
type: index
status: active
tags:
  - decisions
  - resources
---

# 🧭 Decision Log

A **decision log** is different from a note. A note captures *information*. A decision
log captures a *choice*, the reasoning behind it, and — critically — the alternatives
that were considered and rejected.

## Why this folder exists

Agents (and humans re-reading old notes months later) tend to re-litigate settled
questions because there's no record of *why* something was decided a certain way.
Without a trail, the same debate happens again, the same dead-end gets explored again,
and the same mistake can get repeated.

A decision log fixes this by making the **"alternatives rejected"** section mandatory,
not optional. If an agent is about to suggest something, it should check here first —
if the idea was already considered and rejected, the log says so, and why.

## When to create one

Create a decision log entry whenever you (or an agent on your behalf) make a
**non-trivial, hard-to-reverse choice** — not every tiny preference. Good candidates:

- Choosing one architecture/library/tool over another
- Committing to a naming convention, folder structure, or workflow that others will
  build on top of
- Rejecting a feature request, plugin, or integration (and why)
- Any time someone asks "didn't we already decide this?"

Skip it for reversible, low-stakes choices — that's just normal conversation, not a
decision log entry.

## How agents should use this folder

1. Before proposing an architectural change, tool choice, or re-opening a "why don't
   we just..." idea, **search this folder first**.
2. If a matching decision exists and nothing has changed, don't re-propose the
   rejected alternative — reference the existing log entry instead.
3. If a decision needs to be *revisited* (new information, changed constraints), create
   a **new** entry that supersedes the old one — link back to it with `supersedes:`
   in frontmatter. Never silently edit old decisions; keep the history.

## Frontmatter schema

```yaml
---
type: decision
status: active        # active | superseded | reverted
date: YYYY-MM-DD
derived_from: []       # optional: [[Axioms]] or [[Principles]] this follows from
supersedes: ""         # optional: link to an earlier decision this replaces
tags: [decision]
---
```

## Template

See [[TEMPLATE]] for the structure every entry should follow — in particular, the
**Alternatives Rejected** section is required, not optional.

## Related

- [[03-Resources/Principles/README|Principles]] — standing behavioral rules that
  decisions derive from, or that get promoted out of a repeated decision pattern
- [[04-Archives/Memory-Review/Memory-Board.kanban|Memory Review Board]] — where raw
  candidate facts get triaged before some of them graduate into a formal decision here
