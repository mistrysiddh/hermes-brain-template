# Hermes Brain — Obsidian Vault Template for Hermes Agent

A ready-to-use **Obsidian "second brain"** template that pairs with a
[Hermes](https://claude-code.nousresearch.com/docs) AI agent: a human-readable,
version-controllable memory layer on top of Hermes's native session/memory
system.

It gives your agent (and you) a shared place where:

```
Daily/YYYY/MM/DD/*.md   →   Memory-Review/*.md   →   Hermes native MEMORY.md / USER.md
 (raw session archive)      (staged candidate         (durable, injected every
                              facts, human-reviewed)    turn — promoted by hand)
```

- **`Daily/`** — every Hermes session exported as redacted markdown, one file per session, organized by date.
- **`Memory-Review/`** — durable-fact candidates staged for human review before promotion, with an automated dedupe/secret-scrub pass (`consolidate_memory.py`).
- **`Research/`** — working space for in-progress investigation, plus optional local-embedding "trend digest" scripts.
- **`Skills-Notes/`** — index of installed Hermes skills and (if you run a multi-agent setup) teammate profiles.
- **`Projects/`** — one note per active project.
- Preconfigured Obsidian plugins: **Dataview**, **Smart Connections**, **Local REST API**, plus the Tokyo Night theme.

This repo ships as a **template only** — no personal data, chat history, or
API keys are included. See [SETUP.md](SETUP.md) for the full breakdown of
what was intentionally left out.

## Quick start

### Option A — paste into Hermes (easiest)

If you already run a Hermes agent, skip cloning/scripting entirely: open
**[INSTALL_PROMPT.md](INSTALL_PROMPT.md)** and paste one block straight into
your Hermes chat:

- **Prompt 1** — installs the vault only
- **Prompt 2** — sets up the hourly archiving cron job only (vault must already exist)
- **Prompt 3 (master)** — does both in one paste: install the vault, then set
  up the hourly cron job, no follow-up needed

### Option B — run the installer yourself

**Linux / macOS:**
```bash
git clone https://github.com/mistrysiddh/hermes-brain-template.git
cd hermes-brain-template
chmod +x install.sh
./install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/mistrysiddh/hermes-brain-template.git
cd hermes-brain-template
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer asks a few questions — where to put the vault, which local
embedding backend you want for the optional trend-digest scripts (Ollama or
sentence-transformers), and whether to auto-register the vault path with the
Hermes CLI — then finishes the setup for you.

### Option C — full manual control

Follow **[SETUP.md](SETUP.md)** step by step instead of using either installer.

## Cross-platform scripts

| Purpose | Windows | Linux/macOS |
|---|---|---|
| Memory consolidation ("dream cycle") | `python Scripts\consolidate_memory.py` | `python3 Scripts/consolidate_memory.py` |
| Trend digest — Ollama backend | `Scripts\pipeline.ps1` | `Scripts/pipeline.sh` |
| Trend digest — sentence-transformers backend | `Scripts\New-TrendDigest.ps1` | `Scripts/trend_digest.sh` |

## Requirements

- [Obsidian](https://obsidian.md) (free)
- A [Hermes](https://claude-code.nousresearch.com/docs) agent install, if you want the automated session-archive/memory pipeline
- Optional, for the trend-digest scripts: [Ollama](https://ollama.com) *or* Python 3 with `sentence-transformers`

## Security notes

- **Never** commit real vault content back into this template repo — `Daily/`,
  `Memory-Review/*` (except `TEMPLATE.md`), `Research/*` (except `README.md`),
  `.smart-env/`, and all `.obsidian/plugins/*/data.json` files are already
  git-ignored for exactly this reason.
- The Local REST API plugin generates its own API key on first enable —
  store it via your Hermes agent's protected env (`hermes config set
  env.OBSIDIAN_REST_API_KEY "..."`), never as a plaintext note in the vault.
- Run only **one** session-archiving cron job per vault — concurrent writers
  to `Daily/manifest.jsonl` will race and corrupt the index.

## License

MIT — see [LICENSE](LICENSE). Use, fork, and adapt freely.
