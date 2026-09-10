---
type: index
status: active
created: 2026-08-24
tags: [hub, welcome]
---

# Welcome — Hermes Agent Vault

This is the shared Obsidian memory layer for the Hermes agent team (Codex, Ledger, Vox, Argus, and this profile).

Start here: [[Projects/Hermes-Agent-Vault-Setup]] — the master hub note explaining the folder structure, the memory pipeline (Daily → Memory-Review → native memory), and current status/decisions. For topic-based browsing instead of folder-by-folder, see [[MOC]]. For a live at-a-glance view of what's active right now, see [[Dashboard]].

## Folders
- `Projects/` — one note per active project, indexed via [[Projects/README]]
- `Daily/` — raw session archive, `YYYY/MM/DD/`, exported nightly by cron
- `Research/` — active in-progress investigation notes
- `Memory-Review/` — staging area for durable facts before promotion to Hermes native memory
- `Skills-Notes/` — installed skills index + team profile index

Do not store secrets/API keys as plaintext notes in this vault — it syncs via OneDrive. Use Hermes's protected `.env` (`hermes config set env.KEY_NAME "..."`) instead.
