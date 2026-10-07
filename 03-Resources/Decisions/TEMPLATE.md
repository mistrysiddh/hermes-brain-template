---
type: decision
status: active
date: YYYY-MM-DD
derived_from: []
supersedes: ""
tags: [decision]
---

# [Short, specific title — the choice, not the topic]

> Example: "Use Cron/ folder for lock files and run logs instead of Daily/"
> Not: "Cron job improvements"

## Context

What situation forced this decision? What was broken, ambiguous, or in tension?
Keep this to 2-4 sentences — enough for someone (or an agent) with zero memory of
the conversation to understand *why a decision was needed at all*.

## What We Chose

State the decision plainly, in one or two sentences. No hedging — this is the
thing that actually happened.

## Why

The reasoning. What made this the right call *given the constraints at the time*?
Reference any relevant [[03-Resources/Axioms|Axioms]] or
[[03-Resources/Principles/README|Principles]] this derives from, if applicable.

## Alternatives Rejected

**This section is required.** For each alternative seriously considered, one line:
what it was, and why it lost. This is the single most valuable part of the
document — it's what stops the same idea from being re-proposed in six months.

- **Alternative A** — why it was rejected
- **Alternative B** — why it was rejected

## Consequences

What does this choice commit us to? What becomes harder to change later? What
should someone watch out for?

## Status

- `active` — this is the current decision, still in effect
- `superseded` — replaced by a newer decision (link it in frontmatter `supersedes`
  of the *new* entry, not this one)
- `reverted` — explicitly undone; say what caused the reversal
