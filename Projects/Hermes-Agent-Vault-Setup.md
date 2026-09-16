---
type: project
status: active
created: {{date}}
tags: [project, vault-meta]
---

# Hermes Agent Vault Setup

The master hub note for **this vault itself** — its folder structure, the
memory pipeline, and where to find current status/decisions. Referenced
from [[Welcome]], [[MOC]], [[Projects/README|Projects/README]],
[[Research/README|Research/README]], [[Skills-Notes/README|Skills-Notes/README]],
[[SETUP]], and [[Memory-Review/TEMPLATE|Memory-Review/TEMPLATE]] as the
one place that ties the whole layout together.

## Goal

Give an AI agent (or a team of them) a memory it can't forget and you can
actually read — session records land as plain markdown, get deduped and
secret-scrubbed, and are staged for human review before anything becomes
permanent long-term memory. See the root [[README|README]] for the full
pitch.

## Repo / location path

This note lives inside the vault it describes. If you're using the public
template, the upstream repo is
[hermes-brain-template](https://github.com/mistrysiddh/hermes-brain-template);
`update.sh`/`update.ps1` pull new template releases into your installed
copy without touching your personal content.

## Folder structure

- **`Daily/`** — one folder per session date (`Daily/YYYY/MM/DD/`),
  populated by the archiving cron job. See [[Daily/README|Daily/README]].
- **`Memory-Review/`** — staging area for facts pulled out of `Daily/`
  sessions before they're promoted to durable memory. See
  [[Memory-Review/TEMPLATE|Memory-Review/TEMPLATE]].
- **`Projects/`** — one note per active project/repo the agent works on
  (this file is one of them — the vault's own setup counts as a project).
- **`Research/`** — working notes for open-ended research/investigation,
  separate from a specific project.
- **`Skills-Notes/`** — reference docs about the agent's own tooling:
  installed skills, team/agent profiles (if more than one agent uses this
  vault), token usage, vault health.
- **`Dashboard.md`** / **`Dashboard-Beta.md`** — live at-a-glance views of
  the above (active projects, open memory candidates, recent sessions,
  installed skills, token usage, vault health).

## Memory pipeline

`Daily/` session archives → reviewed in `Memory-Review/` → promoted facts
become durable context (either written into [[User-Profile|User-Profile]]
/ this vault's notes directly, or pushed into whatever native memory
system your agent runtime provides, e.g. Hermes's own memory tool).
`Scripts/consolidate_memory.py` automates the first pass of that review;
a human still confirms before anything is treated as permanently true.

## Current status

Template-default state — fill this in with your own vault's specifics
once you've customized it (cron schedule, which optional plugins/scripts
you've enabled, any deviations from the default folder layout).

## Durable decisions

- 

## Next actions

- [ ] 

## Sources used

- 
