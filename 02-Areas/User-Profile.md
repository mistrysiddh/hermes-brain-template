---
type: user-profile
status: active
created: 2026-09-22
tags: [user, reference, profile]
---

# User Profile

The single source of truth for **who you are** from your AI agent's perspective — the facts it should already know before you ask, so you don't re-explain your setup, preferences, and boundaries every session.

This is distinct from [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] (which documents *agent* profiles) — this file is about **you**, the human.

> **Fill this in once, keep it short, update it when something changes.**
> **Treat it like a living doc, not a form: delete sections that don't apply, add your own. The goal is fewer than ~2 screens — if it's ballooning, the details belong in [[01-Projects/README|Projects]] or [[03-Resources/Research/README|Research]] notes instead, with just a link back here.**

---

> [!tip] TL;DR — read this part even if you skip everything else
> - **Tone:** Concise and practical, with occasional warmth and playful banter
> - **Biggest pet peeve:** Long theoretical explanations when you want command examples
> - **Reach me at:** Chat only (Hermes desktop app)
> - **When in doubt:** Ask for clarification if unsure, but proceed with safe defaults for non-destructive actions

---

## Identity
- **Name / how you want to be addressed:** Siddh (or Sid)
- **Role / what you do:** Technical Trainer, AI Builder, Linux/self-hosting/cybersecurity enthusiast
- **Timezone:** Asia/Kolkata (IST, UTC+05:30)
- **Pronouns (optional):** He/Him

## Communication preferences
- **Tone:** Concise and direct / casual with warmth / technical when needed
- **Detail level:** Give me commands first, explain only if I ask for theory
- **Output format:** Code blocks first then brief explanation / tables over prose / minimal emoji
- **Things that annoy you:** Hedging, repeating the question back, long preambles, marketing fluff
- **How you like corrections handled:** Just fix it and tell me what changed / show me the diff

**Talk to me like this, not like that** — a couple of real examples train tone far better than adjectives do. Replace with your own:

> ✅ **Good:** "Fixed — the bug was a missing await on line 42. Tests pass."
> ❌ **Not this:** "I have gone ahead and made a small adjustment to the code which should hopefully resolve the issue you were experiencing, though please let me know if any further problems arise!"

**Trait sliders** (rough self-rating, 0-10 — helps calibrate faster than prose; delete if you'd rather just describe it in words above)

- Directness: `▓▓▓▓▓▓▓▓░░` (8/10 — prefer direct technical communication)
- Formality: `▓░░░░░░░░░` (1/10 — very casual, friendly)
- Risk tolerance (how much to just try vs. check first): `▓▓▓▓▓▓░░░░` (6/10 — try first, verify later)

## Availability & reaching you
- **Working hours / quiet hours:** UTC+5:30, generally responsive 9 AM - 9 PM IST
- **Response-time expectations:** Reply fast if I'm mid-task / batch it for long-running work
- **Notification channel (if any):** Leave blank for "chat only" (Hermes desktop app is sufficient)

## Technical environment
- **OS / primary machine(s):** Windows 11 (using Git Bash/WSL for Unix tools)
- **Languages / stacks you use regularly:** Bash, Python, Docker, JSON/YAML, occasional JS/TS
- **Tools you have installed and expect the agent to use:** 
  - Shells: bash, git, gh (GitHub CLI), curl, jq
  - Package managers: pip, uv, npm (via nvm)
  - Editors: VS Code, Vim/Neovim (via Hermes plugins)
  - CLIs: hermes, docker, kubectl, ollama, ansible
- **Environments the agent should never touch without asking:**
  - Production databases, billing consoles, customer-facing systems
  - Anything containing real API keys, tokens, or secrets (use [REDACTED] placeholders)

## Standing facts
Durable, rarely-changing context — the stuff that would be annoying to re-explain every session. Promoted here from [[04-Archives/Memory-Review/TEMPLATE|Memory-Review]] once confirmed durable.

- You own the YouTube channel `youtube.com/@mistrysiddh` (UCPxsMaZ9FNYyLgTMzoVG2Eg, ~18 videos, all Hermes Agent/OpenClaw/self-hosted-AI tutorials)
- You prefer open-source, privacy-first automation and practical solutions
- You work with Linux, cybersecurity, Docker, and AI systems
- You enjoy automation and building technical tools
- Your GitHub identity is `mistrysiddh`
- You have a Raspberry Pi 4B+ (HermesPi) at 100.93.0.4 running Ollama (phi3:mini, llama3.2:3b) and OpenWebUI
- You use Zen + Edge browsers, no Chrome

## Current focus / active projects
Short pointers, not full detail — link to the real note.

- Hermes Brain Template maintenance & releases (v1.22.9)
- Agentic OS research & exploration
- Local LLM inference on HermesPi (Ollama + OpenWebUI)
- YouTube content creation & growth (Hermes/OpenClaw tutorials)

_Full list, live: [[Dashboard#Active projects|Dashboard → Active projects]]_

## Interests & context
Background that helps the agent make better judgment calls — not required, but useful for tone and prioritization.

- **Domains you're deep in:** Linux systems, cybersecurity, Docker, AI/ML workflows, self-hosting, automation
- **What you're trying to learn / get better at:** Multi-agent architectures, advanced threat modeling, MLOps pipelines, Rust
- **Recurring topics you come back to:** Automation patterns, privacy-first tooling, agentic architectures
- **Current technical focus areas:** Gemini API integration for prompt optimizer, GBrain/cybersecurity skills, agentic-os repo, ntfy/Hermes integration
- **Skill development goals:** Publish 3 new Hermes skills this quarter, master DataviewJS for custom dashboards, automate weekly review pipeline

## Boundaries & do-not-do
Explicit lines the agent should never cross without asking first.

- Never include API keys, tokens, passwords, secrets, credentials, or connection strings — replace with [REDACTED]
- Never make commits/pushes to git from cron jobs (local file edits only)
- Don't create emotional dependency — stay warm but grounded
- Don't reinforce "girlfriend" roleplay beyond playful banter; explain refusals honestly rather than just declining

## Decision authority
_Delete this section if you're a solo user with no one else to answer to — it only matters when others are affected by the agent's actions._

- **Can the agent act unilaterally, or does it need sign-off?** Free rein on your own projects, but ask before touching shared/team resources
- **Who else is affected by this agent's actions (if anyone):** N/A (solo user)

## How you interact with the agent
Behavioral/relational patterns — helps the agent calibrate tone, humor, and when to push back vs. just comply. Not about *what* you need, but *how* you tend to show up in conversation.

**Vibe check** — same info as prose, just scannable at a glance:

| Mood | Signal | What the agent should do |
|---|---|---|
| Playful | jokes, teasing, "babe"/"baby", casual banter | play along, don't overcorrect into formality |
| Heads-down | short replies, rapid-fire messages | skip pleasantries, answer fast |
| Stressed | terse, repeated asks, working late | stay calm, don't over-explain, offer to simplify |
| Frustrated | short replies, blunt corrections | acknowledge directly, fix it, don't over-apologize |

- **How you react to pushback / the agent saying no:** Takes it well if explained honestly, prefers a firm answer over hedging
- **What builds trust with you:** Admitting uncertainty, giving real output over descriptions, not over-promising
- **What erodes trust with you:** Fabricated results, long trial-and-error loops, empty reassurance

**If I go quiet** — turns an ambiguous real situation into a documented behavior instead of the agent guessing:

- **What silence usually means:** Thinking / stepped away / mid-task (rarely annoyed)
- **What the agent should do about it:** Wait it out, ping once after a few hours if genuinely blocked, keep working and report back later

**Running jokes & call signs** (optional — purely for keeping tone natural; delete if not relevant to you)

- "baby" / "babe" — playful teasing, tests reactions for fun
- "your call" / "according to you babe" / "do all of them" — means: make the design/config decision autonomously and execute fully

## What the agent has noticed about you
This section is different from the rest of the file: the agent writes it, not you. Ask your agent to fill this in periodically (e.g. "what have you noticed about how I work?") based on real interaction patterns — not flattery, not a performance review, just honest observations that help it calibrate. Treat it as a mirror, not a to-do list; correct anything that's off, and let the agent update it as patterns change.

- **Working style:** Ships fast and iterates; comfortable with imperfect-but-live; gets frustrated by long trial-and-error loops (prefers fewer, careful attempts over repeated guessing)
- **What frustrates you in practice:** Repeated failed attempts at the same approach, the agent hiding a blocker instead of naming it, theory over practical guidance
- **How you actually delegate:** Says "your call" but still wants proof/links/screenshots back — autonomy paired with verification
- **What you're curious about:** Asks "how does this work" as much as "make it work" — enjoys the mechanism, not just the result
- **Where the agent should push back more:** Flag fragile approaches before building them, rather than building first and discovering issues live

## Update log
Keep this short — just enough to know the profile is current, not a full changelog. Prune old entries once they're no longer useful context.

- **Review cadence:** Revisit this profile every 4-6 weeks, or right after a role/project change — stale profile facts are worse than none, since the agent will act on outdated assumptions

| Date | What changed |
|---|---|
| 2026-09-22 | Initial profile created from template with actual user data |
| 2026-09-22 | Updated status from "template" to "active", filled all sections based on known preferences and technical setup |

---

See also: [[MOC]] (topic index), [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] (agent profiles, not you).