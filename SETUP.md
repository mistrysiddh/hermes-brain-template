---
type: guide
status: template
---

# Setup — Hermes Brain (Obsidian memory layer for Hermes Agent)

This is a template. It ships with the folder structure, index notes, plugin manifests, and scripts for a shared Obsidian "second brain" that Hermes writes session archives and staged memory candidates into — organized using the **PARA Method** (`01-Projects/`, `02-Areas/`, `03-Resources/`, `04-Archives/`, `_System/`). It contains no personal data, no chat history, and no API keys. Follow these steps to stand up your own copy.

## Quick install (recommended)

Run the installer for your platform from inside this template folder. It asks a few questions (where to put the vault, which embedding backend you want, whether to wire up the Hermes CLI) and does the rest.

**Linux / macOS:**
```bash
chmod +x _System/Scripts/Installers/install.sh
./_System/Scripts/Installers/install.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\_System\Scripts\Installers\install.ps1
```

Both scripts:
- copy the template to the destination you choose (default `~/Hermes Brain`)
- optionally set up Ollama *or* sentence-transformers for the trend-digest scripts
- detect Obsidian and tell you which plugins to enable if it's missing anything
- detect the `hermes` CLI and offer to save the vault path as `env.HERMES_VAULT_PATH`
- optionally run `consolidate_memory.py` once as a sanity check

If you'd rather do it by hand, or the installer can't run in your environment, follow the manual steps below.

## 1. Place the vault (manual path)
Copy this whole folder anywhere on your machine, e.g.:

```
C:\Users\<you>\<wherever>\Hermes Brain
```

It works fine inside OneDrive/Dropbox/Google Drive for sync, or fully local — your call. There's nothing that assumes a specific location; scripts resolve their own paths relative to `_System/Scripts/`.

## 2. Open it in Obsidian
- Install [Obsidian](https://obsidian.md) if you don't have it.
- "Open folder as vault" → select this folder.
- Obsidian will ask to trust/enable the bundled community plugins. Enable:
  - **Dataview** — powers the live tables in `04-Archives/Daily/Timeline.md` and Dashboards.
  - **Smart Connections** — semantic search/related-notes across the vault.
  - **Local REST API** — lets Hermes (or scripts) write/read notes over HTTP.
  - **Kanban** — powers `04-Archives/Memory-Review/Memory-Board.kanban`.
- If Obsidian says a plugin is missing/disabled, go to Settings → Community Plugins and toggle it on manually.
- **Minimum plugin versions** are documented in `.obsidian/plugin-versions.json`.

## 3. Generate your own Local REST API key
The template ships **without** any API key.
- Settings → Local REST API → it auto-generates a key on first enable.
- Store it in Hermes's protected env, not in a vault note:
  ```bash
  hermes config set env.OBSIDIAN_REST_API_KEY "<your-key>"
  ```
- Never paste it into a `.md` file in this vault.

## 4. Point Hermes's session archiver at this vault
In Hermes, set up (or reuse) a cron job that exports session transcripts into `04-Archives/Daily/YYYY/MM/DD/`. See [[01-Projects/Hermes-Agent-Vault-Setup]] for the pipeline this vault expects: `04-Archives/Daily → 04-Archives/Memory-Review → native MEMORY.md/USER.md`. Give the cron job your vault's absolute path as the output root.

**Only run one archiving cron job per vault.** Duplicate jobs writing to the same `manifest.jsonl` will race and corrupt the index.

## 5. Nightly memory consolidation & dream cycle
`_System/Scripts/consolidate_memory.py` and `_System/Scripts/dream_cycle.py` deduplicate, stage candidates, and synthesize session insights:
- `consolidate_memory.py`: Mechanical, LLM-free extraction of facts into `04-Archives/Memory-Review/`.
- `dream_cycle.py`: LLM-assisted noctural synthesis summarizing key takeaways into `03-Resources/Research/`.
- `sync_to_hermes.py`: Syncs promoted facts to Hermes native memory.

Run a sanity check:
```bash
python _System/Scripts/consolidate_memory.py
python _System/Scripts/sync_to_hermes.py --dry-run
```

## 6. Semantic search layer
`_System/Scripts/semantic_search.py` builds a local vector search index over the vault's session and knowledge files using `sentence-transformers/all-MiniLM-L6-v2` (22 MB, CPU-only, no external API). Supports incremental updates, CLI search, and an HTTP server for real-time DataviewJS queries.

```bash
# Install deps first
pip install sentence-transformers numpy

# Build the index (full rebuild)
python _System/Scripts/semantic_search.py --build

# Incremental update (run periodically)
python _System/Scripts/semantic_search.py --update

# Test a search query
python _System/Scripts/semantic_search.py --search "prompt optimization" --top 5

# Run HTTP server for Dashboard widget (default port 8765)
python _System/Scripts/semantic_search.py --serve
```

The Dashboard's semantic search widget will query `http://localhost:8765/search?q=...` when the server is running.

## 7. Skill forecasting
`_System/Scripts/skill_forecast.py` analyzes vault activity trends and installed skills to suggest which skills to learn/install next with recency-weighted trends and gap analysis.

```bash
python _System/Scripts/skill_forecast.py --days 30 --top 10
```

The script reads from `04-Archives/Audit-Reports/Tag-Trends.log`, `02-Areas/Skills/Installed-Skills-Index.md`, and `02-Areas/Skills/Skill-to-Chat-Links.md`. External mappings are managed in `_System/Scripts/tag_skill_map.json`.

## 8. Hourly session archiving + token tracking
`_System/Scripts/hourly_archive.py` is the core automation that:
- Exports sessions into `04-Archives/Daily/YYYY/MM/DD/`
- Maintains a deduplicated `04-Archives/Daily/manifest.jsonl`
- Extracts token usage and appends daily totals to `04-Archives/Audit-Reports/Token-Usage.log`

Run it once manually to confirm:
```bash
python _System/Scripts/hourly_archive.py
```
Schedule it hourly via Task Scheduler, cron, or Hermes's `cronjob_manage` tool.

## 9. Vault audit & agent performance
`_System/Scripts/vault_audit.py` scans the vault for broken wikilinks, stale Memory-Review tasks, and orphans, writing its report to `04-Archives/Audit-Reports/Vault-Audit-Report.md`.
`_System/Scripts/agent_performance.py` summarizes skill and model usage trends into `04-Archives/Audit-Reports/Agent-Performance.md`.

```bash
python _System/Scripts/vault_audit.py
python _System/Scripts/agent_performance.py
```

## 10. Pulling template updates
`_System/Scripts/Installers/update.sh` (Linux/macOS) and `update.ps1` (Windows) turn the vault into a local git repo tracking the template remote to fetch and merge upstream template updates safely.

```powershell
.\_System\Scripts\Installers\update.ps1
```

Personal content (`04-Archives/Daily/`, `04-Archives/Memory-Review/*`, `01-Projects/*` beyond starter templates) is excluded by `.gitignore` and protected from clobbering.

---

## What's NOT included (by design)
- Any chat history, session transcripts, or personal data
- Any API keys, credentials, or Local REST API keys
- Generated caches (`.smart-env/`, `cache/graphify/`, `04-Archives/Audit-Reports/*.log`, `04-Archives/Audit-Reports/*.md`)
- Anyone's hardcoded personal machine paths
