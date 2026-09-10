---
type: guide
status: template
---

# Setup — Hermes Brain (Obsidian memory layer for Hermes Agent)

This is a template. It ships with the folder structure, index notes, plugin
manifests, and scripts for a shared Obsidian "second brain" that Hermes writes
session archives and staged memory candidates into — but no personal data,
no chat history, and no API keys. Follow these steps to stand up your own copy.

## Quick install (recommended)

Run the installer for your platform from inside this template folder. It asks
a few questions (where to put the vault, which embedding backend you want,
whether to wire up the Hermes CLI) and does the rest.

**Linux / macOS:**
```bash
chmod +x install.sh
./install.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Both scripts:
- copy the template to the destination you choose (default `~/Hermes Brain`)
- optionally set up Ollama *or* sentence-transformers for the trend-digest scripts
- detect Obsidian and tell you which plugins to enable if it's missing anything
- detect the `hermes` CLI and offer to save the vault path as `env.HERMES_VAULT_PATH`
- optionally run `consolidate_memory.py` once as a sanity check

If you'd rather do it by hand, or the installer can't run in your environment,
follow the manual steps below.

## 1. Place the vault (manual path)
Copy this whole folder anywhere on your machine, e.g.:

```
C:\Users\<you>\<wherever>\Hermes Brain
```

It works fine inside OneDrive/Dropbox/Google Drive for sync, or fully local —
your call. There's nothing that assumes a specific location; scripts resolve
their own paths relative to `Scripts/`.

## 2. Open it in Obsidian
- Install [Obsidian](https://obsidian.md) if you don't have it.
- "Open folder as vault" → select this folder.
- Obsidian will ask to trust/enable the bundled community plugins. Enable:
  - **Dataview** — powers the live tables in `Daily/Timeline.md` etc.
  - **Smart Connections** — semantic search/related-notes across the vault.
  - **Local REST API** — lets Hermes (or scripts) write/read notes over HTTP.
  - **brain-atlas** (if present) — vault-specific helper plugin.
- If Obsidian says a plugin is missing/disabled, go to Settings → Community
  Plugins and toggle it on manually — first-run enable state isn't always
  picked up automatically after a fresh copy.

## 3. Generate your own Local REST API key
The template ships **without** any API key (the original had a leaked one —
don't reuse example keys you find anywhere online, always generate fresh).
- Settings → Local REST API → it auto-generates a key on first enable.
- Store it in Hermes's protected env, not in a vault note:
  ```
  hermes config set env.OBSIDIAN_REST_API_KEY "<your-key>"
  ```
- Never paste it into a `.md` file in this vault — it syncs wherever the
  vault syncs (OneDrive, git, etc).

## 4. Point Hermes's session archiver at this vault
In Hermes, set up (or reuse) a cron job that exports session transcripts into
`Daily/YYYY/MM/DD/`. See [[Projects/Hermes-Agent-Vault-Setup]] for the
pipeline this vault expects: `Daily → Memory-Review → native MEMORY.md/USER.md`.
Give the cron job your vault's absolute path as the output root.

**Only run one archiving cron job per vault.** Duplicate jobs writing to the
same `Daily/manifest.jsonl` will race and corrupt the index.

## 5. (Optional) Nightly memory consolidation
`Scripts/consolidate_memory.py` is a mechanical, LLM-free "dream cycle" that
dedupes and stages memory candidates. It never writes to Hermes's native
memory — that promotion step stays a manual human decision, per
[[Memory-Review/TEMPLATE]].

Run it once manually first to confirm it works before trusting a cron:
```
python Scripts/consolidate_memory.py "<path-to-this-vault>"
```
Then schedule it nightly if you like the output.

## 6. (Optional) Trend digest scripts
Build a "what's relevant right now" digest from your notes using local
embeddings — pick whichever backend you already have set up:

| Backend | Windows | Linux/macOS |
|---|---|---|
| Ollama (`nomic-embed-text`, no Python deps) | `Scripts\pipeline.ps1` | `Scripts/pipeline.sh` |
| sentence-transformers (pure Python) | `Scripts\New-TrendDigest.ps1` | `Scripts/trend_digest.sh` |

All of them default to `<this vault>/Research/Trend-Digest/` for output and
resolve the vault path relative to their own location, so they work out of
the box — pass a vault path / query / top-N as arguments (or
`-VaultPath`/`-Query` on Windows) to override.

```bash
# Linux/macOS examples
./Scripts/pipeline.sh                       # Ollama backend, defaults
./Scripts/trend_digest.sh . "docker security" 10
```

## 7. Start writing
Read [[Welcome]] and [[MOC]] for orientation, then let sessions accumulate in
`Daily/` naturally. Review `Memory-Review/Promotion-Candidates.md` (created on
first consolidation run) periodically and promote durable facts into Hermes's
real memory by hand.

## 8. (Optional) Pulling in later template updates
`install.sh`/`install.ps1` do a one-shot copy — there's no `.git` in the
destination, so there was previously no safe way to pull in template
changes (a new script, an updated bundled plugin, a fixed bug) without
risking an overwrite of anything you'd hand-edited.

`update.sh` / `update.ps1` fix this: run one from inside your installed
vault (not the template) and it turns the vault into a local git repo
tracking the template as a read-only remote, then fetches and merges.
git's own 3-way merge surfaces a conflict on any file you changed
yourself instead of silently clobbering it — resolve those like any git
merge conflict, then commit.

```bash
./update.sh                 # Linux/macOS — first run sets everything up
```
```powershell
.\update.ps1                 # Windows
```

Your personal content (`Daily/`, `Memory-Review/*`, `Projects/*` beyond
`README.md`, plugin `data.json` files, etc.) is protected the same way it
always was — this vault's own `.gitignore` already excludes it, so it
never enters the diff/merge at all. The `template` remote this creates
also has push disabled on purpose: this is a one-way pull, never a way
for your vault's content to leave the machine.

---

## What's NOT included (by design)
- Any chat history, session archives, or Supermemory exports
- Any API keys, tokens, or `.obsidian/plugins/*/data.json` settings
- Generated caches (`.smart-env/`, `graphify-out/`)
- Anyone's personal file paths — everything here is relative/portable

If you find a leftover personal path or credential anywhere in this template,
that's a bug — please strip it before distributing further.
