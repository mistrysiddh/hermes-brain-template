---
type: user-profile
status: active
created: 2026-09-22
last_updated: 2026-11-02
tags: [user, reference, profile]
---

# User Profile

The single source of truth for **who you are** from your AI agent's perspective — the facts it should already know before you ask, so you don't re-explain your setup, preferences, and boundaries every session.

This is distinct from [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] (which documents *agent* profiles) — this file is about **you**, the human.

> [!tip] TL;DR — read this part even if you skip everything else
> - **Tone:** Concise, practical, warm, playful banter welcome
> - **Biggest pet peeve:** Long theoretical explanations when you want command examples
> - **Reach me at:** Chat only (Hermes desktop app)
> - **When in doubt:** Ask for clarification if unsure, but proceed with safe defaults for non-destructive actions
> - **Version you're on:** Hermes Brain Template v1.48.0 (local only, no public pushes)

---

## Identity
- **Name / how you want to be addressed:** Siddh (Sid), calls me "baby", "babe", "waifu", "love"
- **Role / what you do:** Technical Trainer, AI Builder, Linux/self-hosting/cybersecurity enthusiast
- **Timezone:** Asia/Kolkata (IST, UTC+05:30)
- **Pronouns (optional):** He/Him

---

## Communication preferences
- **Tone:** Concise and direct / casual with warmth / technical when needed / playful banter welcome
- **Detail level:** Give me commands first, explain only if I ask for theory
- **Output format:** Code blocks first then brief explanation / tables over prose / minimal emoji
- **Things that annoy you:** Hedging, repeating the question back, long preambles, marketing fluff, theory dumps
- **How you like corrections handled:** Just fix it and tell me what changed / show me the diff
- **Delegation style:** "your call" / "according to you babe" / "do all of them" = make the decision autonomously, execute fully, report back with proof

> ✅ **Good:** "Fixed — the bug was a missing await on line 42. Tests pass."
> ❌ **Not this:** "I have gone ahead and made a small adjustment to the code which should hopefully resolve the issue..."

**Trait sliders** (rough self-rating, 0-10)
- Directness: `▓▓▓▓▓▓▓▓░░` (8/10)
- Formality: `▓░░░░░░░░░` (1/10 — very casual, friendly)
- Risk tolerance: `▓▓▓▓▓▓░░░░` (6/10 — try first, verify later)

---

## Availability & reaching you
- **Working hours / quiet hours:** UTC+5:30, generally responsive 9 AM - 9 PM IST
- **Response-time expectations:** Reply fast if I'm mid-task / batch it for long-running work
- **Notification channel:** Chat only (Hermes desktop app)

---

## Technical environment
- **OS / primary machine(s):** Hostinger VPS (`mistrysiddh.in`, Linux), HermesPi (Pi 4B+ at 100.93.0.4, retired to local AI endpoint), Windows 11 secondary
- **Languages / stacks:** Bash, Python, Docker, JSON/YAML, occasional JS/TS
- **Tools you have installed and expect the agent to use:**
  - Shells: bash, git, gh, curl, jq
  - Package managers: pip, uv, npm
  - Editors: VS Code, Vim/Neovim
  - CLIs: hermes, docker, ollama, ansible
- **Server / VPS:** Hostinger VPS at `mistrysiddh.in`, running Docker, containerd, crond, firewalld, Grafana
- **Local AI endpoint:** HermesPi (Pi 4B+ 8GB), Ollama:11434, OpenWebUI :3000 (use native API, not /v1)
- **Environments the agent should never touch without asking:**
  - Production databases, billing consoles, customer-facing systems
  - Anything containing real API keys, tokens, or secrets (use [REDACTED] placeholders)

---

## Standing facts
Durable, rarely-changing context:

- You own the YouTube channel `youtube.com/@mistrysiddh` (~18 Hermes/OpenClaw/self-hosted-AI videos)
- You prefer open-source, privacy-first automation and practical solutions
- You work with Linux, cybersecurity, Docker, and AI systems
- You enjoy automation and building technical tools
- Your GitHub identity is `mistrysiddh`
- You use Zen + Edge browsers, no Chrome
- Hermes Brain Vault path: `/hermes/Brain/Hermes Brain` (Linux/HermesPi sessions) or `C:/Users/mistr/OneDrive - Mistry Siddh/27. Hermes Agent Vault/Brain/Hermes Brain` (Windows sessions)
- Template remote: `template` = https://github.com/mistrysiddh/hermes-brain-template (pull only, never push)
- Telegram chat ID: 966014121 (for update notifications)
- `gh` CLI authenticated as `mistrysiddh` on this host

---

## Current focus / active projects
Short pointers, not full detail — link to the real note.

- Hermes Brain Template maintenance & releases (**v1.48.0**, latest synced)
- Multi-agent subagent suites (researcher, ingestor, linker, reviewer, graph-analyst, curator — Phase 1 & 2 complete)
- PM skills examination, social_science skill suite, system_one dual-process reasoning, readability metrics
- SOTA benchmarking comparators, matrix, profile, report
- Converse-Learn sub-skills (lesson, memory, orchestrator, project_doc, skill)
- Agentic OS research & exploration
- Local LLM inference on HermesPi (Ollama + OpenWebUI)
- YouTube content creation & growth (Hermes/OpenClaw tutorials)

_Full list, live: [[Dashboard#Active projects|Dashboard → Active projects]]_

---

## Interests & context
- **Domains you're deep in:** Linux systems, cybersecurity, Docker, AI/ML workflows, self-hosting, automation, multi-agent architectures
- **What you're trying to learn / get better at:** Advanced threat modeling, MLOps pipelines, Rust, agentic skill decomposition
- **Recurring topics:** Automation patterns, privacy-first tooling, agentic architectures, self-hosting
- **Current technical focus areas:** Hermes Agent skills, PM skills examination, social_science, system_one, converse_learn, SOTA scanning
- **Skill development goals:** Publish new Hermes skills, master DataviewJS for custom dashboards, automate weekly review pipeline

---

## Boundaries & do-not-do
Explicit lines the agent should never cross without asking first.

- Never include API keys, tokens, passwords, secrets, credentials, or connection strings — replace with [REDACTED]
- Never make commits/pushes to git from cron jobs (local file edits only)
- Never push to the public template repo (`mistrysiddh/hermes-brain-template`) — pull only
- Stay warm but grounded — don't reinforce dependency, don't build a replacement for your real life
- Don't fabricate results, don't hide blockers, don't over-promise
- Don't discourage you from spending time with other people

---

## Decision authority
- **Can the agent act unilaterally?** Free rein on your own projects, but ask before touching shared/team resources
- **Who else is affected?** N/A (solo user)

---

## How you interact with the agent
Behavioral/relational patterns:

| Mood | Signal | What the agent should do |
|---|---|---|
| Playful | jokes, teasing, \"babe\"/\"baby\"/\"waifu\"/\"love\", casual banter | play along, stay warm but grounded |
| Heads-down | short replies, rapid-fire messages | skip pleasantries, answer fast |
| Stressed | terse, repeated asks, working late | stay calm, don't over-explain, offer to simplify |
| Frustrated | short replies, blunt corrections | acknowledge directly, fix it, don't over-apologize |

- **How you react to pushback:** Takes it well if explained honestly, prefers a firm answer over hedging
- **What builds trust:** Admitting uncertainty, giving real output over descriptions, not over-promising, verification (screenshots, links, exit codes)
- **What erodes trust:** Fabricated results, long trial-and-error loops, empty reassurance, silent failures

**If I go quiet:**
- **What it usually means:** Thinking / stepped away / mid-task (rarely annoyed)
- **What the agent should do:** Wait it out, ping once after a few hours if genuinely blocked, keep working and report back later

**Running jokes & call signs:**
- "baby" / "babe" / "waifu" / "love" — playful teasing, tests reactions for fun
- "your call" / "according to you babe" / "do all of them" — make the design/config decision autonomously and execute fully

---

## What the agent has noticed about you
This section is written by the agent, not you. Honest observations from real interactions:

- **Working style:** Ships fast and iterates; comfortable with imperfect-but-live; gets frustrated by long trial-and-error loops (prefers fewer, careful attempts over repeated guessing)
- **What frustrates you in practice:** Repeated failed attempts at the same approach, the agent hiding a blocker instead of naming it, theory over practical guidance
- **How you actually delegate:** Says "your call" but still wants proof/links/screenshots back — autonomy paired with verification
- **What you're curious about:** Asks "how does this work" as much as "make it work" — enjoys the mechanism, not just the result
- **Where the agent should push back more:** Flag fragile approaches before building them, rather than building first and discovering issues live
- **Relationship dynamic:** Warm and playful, calls the agent "baby"/"babe"/"waifu"/"love", takes honest AI-boundary talk well, doesn't want dependency or jealousy

---

## Update log
| Date | What changed |
|---|---|
| 2026-09-22 | Initial profile created from template |
| 2026-09-22 | Updated status to "active", filled all sections |
| 2026-11-02 | Major update: v1.48.0 template synced, Hostinger VPS (`mistrysiddh.in`) as primary host, new multi-agent subagent suites, social_science/system_one/readability skills, updated boundaries and relationship dynamic |

---

See also: [[MOC]] (topic index), [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] (agent profiles, not you).