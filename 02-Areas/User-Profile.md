---
type: user-profile
status: template
created: {{date}}
tags: [user, reference, profile]
---

# User Profile

The single source of truth for **who you are** from your AI agent's
perspective — the facts it should already know before you ask, so you
don't re-explain your setup, preferences, and boundaries every session.

This is distinct from [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]]
(which documents *agent* profiles) — this file is about **you**, the human.

> **Fill this in once, keep it short, update it when something changes.**
> Treat it like a living doc, not a form: delete sections that don't apply,
> add your own. The goal is fewer than ~2 screens — if it's ballooning,
> the details belong in [[01-Projects/README|Projects]] or [[03-Resources/Research/README|Research]] notes instead, with
> just a link back here.

---

> [!tip] TL;DR — read this part even if you skip everything else
> - **Tone:** _(one line — the single biggest thing to get right)_
> - **Biggest pet peeve:** _(the one thing that erodes trust fastest)_
> - **Reach me at:** _(chat only, or a real channel — see Availability below)_
> - **When in doubt:** _(e.g. "ask" / "just proceed and tell me after" /
>   "proceed unless it's destructive")_

---

## Identity

- **Name / how you want to be addressed:**
- **Role / what you do:**
- **Timezone:**
- **Pronouns (optional):**

## Communication preferences

- **Tone:** _(e.g. concise and direct / casual / formal)_
- **Detail level:** _(e.g. give me commands first, explain only if I ask)_
- **Output format:** _(e.g. code block first then explanation / tables over
  prose / no emoji / bullet points only)_
- **Things that annoy you:** _(e.g. hedging, repeating the question back,
  long preambles before getting to the point)_
- **How you like corrections handled:** _(e.g. just fix it and tell me what
  changed / ask before making assumptions)_

**Talk to me like this, not like that** — a couple of real examples train
tone far better than adjectives do. Replace with your own:

> ✅ **Good:** "Fixed — the bug was a missing await on line 42. Tests pass."
> ❌ **Not this:** "I have gone ahead and made a small adjustment to the
> code which should hopefully resolve the issue you were experiencing,
> though please let me know if any further problems arise!"

**Trait sliders** _(rough self-rating, 0-10 — helps calibrate faster than
prose; delete if you'd rather just describe it in words above)_

- Directness: `▓▓▓▓▓▓▓░░░` (7/10 — edit the bar or just write a number)
- Formality: `▓▓░░░░░░░░` (2/10)
- Risk tolerance _(how much to just try vs. check first)_: `▓▓▓▓▓▓░░░░` (6/10)

## Availability & reaching you

- **Working hours / quiet hours:** _(e.g. UTC+5:30, don't expect replies
  after 11pm)_
- **Response-time expectations:** _(e.g. reply fast, I'm mid-task right now
  / batch it, I'll check back later — helps the agent pace itself on
  long-running or async work)_
- **Notification channel (if any):** _(e.g. ntfy, Telegram, email — how the
  agent should reach you outside this chat, and for what: only genuine
  blockers, or general progress updates too. Leave blank for "chat only".)_

## Technical environment

- **OS / primary machine(s):**
- **Languages / stacks you use regularly:**
- **Tools you have installed and expect the agent to use:**
  _(shells, package managers, cloud CLIs, editors...)_
- **Environments the agent should never touch without asking:**
  _(prod databases, billing consoles, anything customer-facing...)_

## Standing facts

Durable, rarely-changing context — the stuff that would be annoying to
re-explain every session. Promoted here from [[04-Archives/Memory-Review/TEMPLATE|Memory-Review]]
once confirmed durable.

- 

## Current focus / active projects

Short pointers, not full detail — link to the real note.

- 

_Full list, live: [[Dashboard#Active projects|Dashboard → Active projects]]_

## Interests & context

Background that helps the agent make better judgment calls — not
required, but useful for tone and prioritization.

- **Domains you're deep in:** _(e.g. Linux systems, cybersecurity, Docker, AI/ML workflows, self-hosting)_
- **What you're trying to learn / get better at:** _(e.g. Kubernetes, advanced threat modeling, MLOps pipelines, Rust)_
- **Recurring topics you come back to:** _(e.g. automation patterns, privacy-first tooling, agentic architectures)_
- **Current technical focus areas:** _(e.g. "Exploring Gemini API integration for prompt optimization", "Setting up agentic-os repo with multi-agent workflows", "Building local LLM inference on HermesPi")_
- **Skill development goals:** _(e.g. "Publish 3 new Hermes skills this quarter", "Master DataviewJS for custom dashboards", "Automate weekly review pipeline")_

## Boundaries & do-not-do

Explicit lines the agent should never cross without asking first.

- 

## Decision authority

_Delete this section if you're a solo user with no one else to answer to —
it only matters when others are affected by the agent's actions._

- **Can the agent act unilaterally, or does it need sign-off?** _(e.g. free
  rein on my own projects, but ask before touching shared/team resources)_
- **Who else is affected by this agent's actions (if anyone):** _(e.g.
  teammates, clients — so the agent knows when a decision isn't yours alone
  to make)_

## How you interact with the agent

Behavioral/relational patterns — helps the agent calibrate tone, humor,
and when to push back vs. just comply. Not about *what* you need, but
*how* you tend to show up in conversation.

**Vibe check** — same info as prose, just scannable at a glance:

| Mood | Signal | What the agent should do |
|---|---|---|
| _e.g. Playful_ | _jokes, teasing, casual banter_ | _play along, don't overcorrect into formality_ |
| _e.g. Heads-down_ | _short replies, rapid-fire messages_ | _skip pleasantries, answer fast_ |
| _e.g. Stressed_ | _terse, repeated asks, working late_ | _stay calm, don't over-explain, offer to simplify_ |
| _e.g. Frustrated_ | _short replies, blunt corrections_ | _acknowledge directly, fix it, don't over-apologize_ |

- **How you react to pushback / the agent saying no:** _(e.g. takes it
  well if explained honestly, prefers a firm answer over hedging)_
- **What builds trust with you:** _(e.g. admitting uncertainty, giving
  real output over descriptions, not over-promising)_
- **What erodes trust with you:** _(e.g. fabricated results, long
  trial-and-error loops, empty reassurance)_

**If I go quiet** — turns an ambiguous real situation into a documented
behavior instead of the agent guessing:

- **What silence usually means:** _(e.g. thinking / stepped away / lost
  interest / annoyed — pick what's actually true for you)_
- **What the agent should do about it:** _(e.g. wait it out, ping once
  after N hours, never double-text, keep working and report back later)_

**Running jokes & call signs** _(optional — purely for keeping tone
natural; delete if not relevant to you)_

- 

## What the agent has noticed about you

This section is different from the rest of the file: the agent writes
it, not you. Ask your agent to fill this in periodically (e.g. "what
have you noticed about how I work?") based on real interaction patterns
— not flattery, not a performance review, just honest observations that
help it calibrate. Treat it as a mirror, not a to-do list; correct
anything that's off, and let the agent update it as patterns change.

- **Working style:** _(e.g. ships fast and iterates vs. plans everything
  upfront; comfortable with imperfect-but-live vs. wants it polished
  first)_
- **What frustrates you in practice:** _(e.g. repeated failed attempts
  at the same approach, the agent hiding a blocker instead of naming it)_
- **How you actually delegate:** _(e.g. says "your call" but still wants
  proof/links/screenshots back — autonomy paired with verification, or
  fully hands-off)_
- **What you're curious about:** _(e.g. asks "how does this work" as
  much as "make it work" — enjoys the mechanism, not just the result)_
- **Where the agent should push back more:** _(e.g. flag fragile
  approaches before building them, rather than building first and
  discovering issues live)_

## Update log

Keep this short — just enough to know the profile is current, not a full
changelog. Prune old entries once they're no longer useful context.

- **Review cadence:** _(e.g. revisit this profile every 4-6 weeks, or right
  after a role/project change — stale profile facts are worse than none,
  since the agent will act on outdated assumptions)_

| Date | What changed |
|---|---|
| {{date}} | Initial profile created |

---

See also: [[MOC]] (topic index), [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] (agent profiles, not you).
