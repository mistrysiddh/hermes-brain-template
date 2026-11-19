---
title: Refactoring Frameworks Feature Checklist
type: guide
status: active
tags: [refactoring, checklist, features, discussion-40]
---

# Feature Checklist: Refactoring Frameworks Applied to Thinking

Drafted for [Discussion #40](https://github.com/mistrysiddh/hermes-brain-template/discussions/40)
— "Can we apply refactoring frameworks to thinking"

Source: `pm_github_skills_table.md` shared by @TomLucidor — maps software-design thinkers to agent skills
across single-author / majority-author / multi-author grades.

Goal: turn each refactoring framework into a Hermes Brain agent skill (multi-harness compliant:
`--vault`, deferred `init_paths()`, `--dry-run` default, `--apply`, stdlib-only, `--test`).

---

## Coverage by Framework

| # | Framework | Thinker(s) | Already in Hermes? | Gap | Proposed new skill | Priority |
|---|-----------|------------|-------------------|-----|-------------------|----------|
| 1 | TDD + Test Desiderata | Kent Beck | Partial — `unstuck_decide.py` (decide workflow), `skill_pack/adaptive_practice.py` | No dedicated TDD red/green/refactor loop for vault work | `tdd-loop.py` — red/green/refactor cycle for vault edits + skill changes | Tier 1 |
| 2 | Tidy First / tidying | Kent Beck | No | No structural-vs-behavioral change separation | `tidy-first.py` — structure-only PRs, tidyings before behavioral changes | Tier 1 |
| 3 | Refactoring catalog (66 refactorings) | Martin Fowler | No | No catalog of named refactorings applied to vault notes/scripts | `refactor-catalog.py` — extract method, rename, move, inline, etc. on vault content | Tier 1 |
| 4 | Working Effectively with Legacy Code | Michael Feathers | Partial — `self_critique.py` finds issues but no seam/characterization-test workflow | No characterization tests, seam detection, dependency breaking | `legacy-seams.py` — seam finding, characterization tests, safe-legacy-change workflow | Tier 2 |
| 5 | POODR rules / 99 Bottles | Sandi Metz | No | No OOP design rule checking for vault scripts | `sandi-metz-reviewer.py` — POODR + 99 Bottles rule checks on Python scripts | Tier 2 |
| 6 | SOLID + Clean Architecture | Robert C. Martin | Partial — `self_critique.py` script hygiene | No SOLID principle scoring for vault architecture | `solid-review.py` — SRP/OCP/LSP/ISP/DIP scoring per script/module | Tier 2 |
| 7 | Design by Contract | Bertrand Meyer | No | No pre/post-condition enforcement on skills | `dbc-enforcer.py` — DBC contracts for skill function entry/exit | Tier 3 |
| 8 | CQRS / Event Sourcing | Greg Young | No | No command/query separation in vault sync flows | `cqrs-sync.py` — CQRS split for memory sync + event log | Tier 3 |
| 9 | Continuous Delivery / Farley Score | Dave Farley | No | No test-quality scoring (Farley's 8 properties) | `farley-score.py` — test-quality scorecard for vault test suites | Tier 3 |
| 10 | Domain-Driven Design | Vaughn Vernon / Eric Evans | Partial — `knowledge_management.py` (ontology, datasets) | No bounded-context / context-mapping workflow | `ddd-bounded-context.py` — context mapping, ubiquitous language enforcement | Tier 3 |
| 11 | Evolutionary Naming / Naming as a Process | Arlo Belshee | No | No naming-quality improvement workflow | `evolutionary-naming.py` — 6-step naming process for vault entities | Tier 3 |
| 12 | Approval / Golden-master testing | Llewellyn Falco / Emily Bache | No | No approval-test workflow for skill outputs | `approval-tests.py` — golden-master comparison for skill report outputs | Tier 3 |
| 13 | Strangler Fig pattern | Martin Fowler | No | No incremental migration path for legacy vault scripts | `strangler-fig.py` — incremental replacement of legacy scripts | Tier 3 |

---

## Phase 1 — Build first (highest leverage)

These address the biggest gaps and build on skills we already have:

1. **`tidy-first.py`** — Separates structural cleanups from behavioral changes. Pairs naturally with `self_critique.py` findings (run tidyings first, then apply fixes).
2. **`tdd-loop.py`** — Red-green/refactor loop for vault edits. Complements `adaptive_practice.py` (already builds practice problems).
3. **`refactor-catalog.py`** — Named refactorings (extract method, rename, inline) for vault notes and scripts. Direct Fowler mapping.

Each skill:
- Accepts `--vault <path>`
- Resolves paths in `main()` via `init_paths()` — never module-level
- Runs `--dry-run` by default
- `--apply` requires per-fix human approval
- Stdlib-only
- `--test` self-tests (4/4 minimum)

---

## How This Connects to Existing Work

- **`self_critique.py`** → findings feed `tidy-first.py` (structural) then `refactor-catalog.py` (behavioral fixes)
- **`unstuck_decide.py`** → the "decide" workflow pairs with TDD test-writing decisions
- **`adaptive_practice.py`** → practice-problem generation for TDD learners
- **`knowledge_management.py`** → DDD ontology work extends to bounded contexts

---

## Next Step

Ready to start with **Phase 1: `tidy-first.py`** — it's the smallest, cleanest build and unblocks everything after it (you can't refactor safely until you've tidied).

Want me to start building `tidy-first.py`? No pressure — just say the word. ❤️