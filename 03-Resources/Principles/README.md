---
type: index
status: active
tags:
  - principles
  - resources
---

# 📐 Principles

A **principle** is a standing behavioral rule — more durable than a single decision,
derived from an [[03-Resources/Axioms|Axiom]] or distilled from a pattern of repeated
decisions.

Where a [[03-Resources/Decisions/README|Decision]] is "we chose X on this date for
these reasons," a principle is "we always do X" or "we never do Y" — the kind of rule
that should apply to *future* decisions without re-litigating the reasoning every time.

## How a principle gets created

Principles aren't written speculatively — they get **promoted** from evidence:

1. You notice the same kind of decision keeps getting made the same way (e.g.
   "we keep choosing to hold uploads until the user explicitly says go")
2. That pattern gets written up here as an explicit principle, with a link back to
   the decision(s) it was distilled from (`derived_from:` in frontmatter, pointing the
   other direction — decisions link up to the axiom, principles link down to the
   decisions that proved them out)
3. From then on, agents check principles *before* making a similar decision, instead
   of re-deriving the same reasoning from scratch

## Frontmatter schema

```yaml
---
type: principle
status: active        # active | deprecated
derived_from: ""       # the Axiom this follows from, if any
evidenced_by: []        # decisions that demonstrate/justify this principle
tags: [principle]
---
```

## How agents should use this folder

Before proposing a workflow change, check if a principle already governs it. If a
principle says "never commit personal data to the public template" and an agent is
about to stage a file with real session content, that's a hard stop — the principle
should win over a one-off convenience argument.

## Related

- [[03-Resources/Axioms|Axioms]] — the small set of foundational beliefs principles
  derive from
- [[03-Resources/Decisions/README|Decision Log]] — the choices that principles get
  distilled from, and that principles constrain going forward
