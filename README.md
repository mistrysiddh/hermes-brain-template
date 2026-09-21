# Hermes Brain — Obsidian Vault Template for Hermes Agent (including OpenClaw)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](docs/LICENSE)
[![Made for Obsidian](https://img.shields.io/badge/Made%20for-Obsidian-7C3AED.svg)](https://obsidian.md)
[![Works with Hermes](https://img.shields.io/badge/Works%20with-Hermes%20Agent-1DA1F2.svg)](https://claude-code.nousresearch.com/docs)
[![Works with OpenClaw](https://img.shields.io/badge/Works%20with-OpenClaw-FF6B35.svg)](https://claude-code.nousresearch.com/docs)
[![Lint Scripts](https://github.com/mistrysiddh/hermes-brain-template/actions/workflows/lint.yml/badge.svg)](https://github.com/mistrysiddh/hermes-brain-template/actions/workflows/lint.yml)
[![Changelog](https://img.shields.io/badge/Changelog-latest-blue.svg)](docs/CHANGELOG.md)
[![User Profile](https://img.shields.io/badge/User%20Profile-documented-2EA043.svg)](02-Areas/User-Profile.md)

**Give your Hermes/OpenClaw agent a memory it can't forget — and you can actually read.**

Every session your agent runs gets archived as plain markdown, deduped and
secret-scrubbed automatically, and staged for you to review before anything
becomes permanent. No black box, no vendor lock-in — it's just an Obsidian
vault, so you can search it, link it, graph it, and back it up like any
other notes.

![Hermes Brain graph view](assets/graph-view-screenshot.png)

## Why this instead of nothing?

- **You stop losing context.** Every Hermes session gets archived automatically — nothing lives only in a chat log you'll never scroll back to.
- **You stay in control of what becomes "memory."** Nothing gets promoted to Hermes's real memory without a human reading and approving it first.
- **It's just markdown.** Open it in Obsidian, `grep` it, put it in git, read it in Notepad — no proprietary format, no export step.
- **Set up once, in one paste.** A single prompt into your Hermes chat installs the vault *and* wires up hourly archiving — see below.

## Why this instead of [alternative]?

| | Hermes Brain | Raw chat logs | Vector-DB memory (e.g. Mem0) | Generic Obsidian PKM |
|---|---|---|---|---|
| **Human review before "memory"** | ✅ staged in `04-Archives/Memory-Review/`, nothing auto-promotes | ❌ nothing structured | ❌ auto-embedded, opaque | N/A — no agent pipeline |
| **Readable without special tooling** | ✅ plain markdown | ✅ but unstructured | ❌ needs the vendor's UI/API | ✅ |
| **Portable / no vendor lock-in** | ✅ your files, your git repo | ✅ | ❌ tied to the service | ✅ |
| **Built-in agent-usage analytics** | ✅ token usage, vault audit, agent performance — all in `Dashboard.md` | ❌ | Varies | ❌ |
| **Zero setup for a Hermes agent specifically** | ✅ one-paste install prompt | N/A | ❌ separate integration work | ❌ generic, no agent wiring |

Use a vector-DB memory service if you want the agent to auto-recall
semantically similar things with zero human-in-the-loop. Use this
template if you want to **see and approve** what your agent remembers,
in a format you already own.

## What's inside

```
04-Archives/Daily/YYYY/MM/DD/*.md   →   04-Archives/Memory-Review/*.md   →   Hermes native MEMORY.md / USER.md
     (raw session archive)                    (staged candidate                 (durable, injected every
                                            facts, human-reviewed)            turn — promoted by hand)
```

The vault is structured according to the **PARA Method** (Projects, Areas, Resources, Archives) with a dedicated `_System/` core:

- **`01-Projects/`** — Active projects with goals and deadlines, architectural decision records (`01-Projects/ADR/`), and an Obsidian Dataview database (`Projects.base`).
- **`02-Areas/`** — Long-term standards, human alignment parameters (`02-Areas/User-Profile.md`), installed skills catalog, team roster, and the 11-dimension [[02-Areas/Skills/Personality-Judgment-Framework|Personality Judgment Framework]].
- **`03-Resources/`** — Domain knowledge hubs ([[03-Resources/MOCs/Technology-Stack-MOC|Technology Stack]], [[03-Resources/MOCs/Cybersecurity-MOC|Cybersecurity]], [[03-Resources/MOCs/AI-ML-MOC|AI/ML]], [[03-Resources/MOCs/Agentic-Architecture-MOC|Agentic Architecture]]), technical research inquiries (`03-Resources/Research/`), and reference guides (`03-Resources/Guides/`).
- **`04-Archives/`** — Historical and completed items: [[04-Archives/Daily/Timeline|Daily Session Timeline]], [[04-Archives/Daily/Chat-Correlation|Chat Correlation]], 3-stage memory staging ([[04-Archives/Memory-Review/Memory-Board.kanban|Memory Kanban]]), and telemetry/audit reports (`04-Archives/Audit-Reports/`).
- **`_System/`** — Operational core: Reusable note templates (`_System/Templates/`), cross-platform automation scripts (`_System/Scripts/`), and visual architecture canvases (`_System/Canvases/Memory-Pipeline.canvas`).
- **`Dashboard.md` & `_System/Canvases/Dashboard-Beta.md`** — Live command centers providing immediate visibility into active projects, token telemetry, archiver health, recent sessions, and skill analytics.
- Preconfigured Obsidian plugins: **Dataview**, **Smart Connections**, **Local REST API**, **Kanban**, plus two bundled themes — **Tokyo Night** and **Nemoclaw**.

This repo ships as a **template only** — no personal data, chat history, or
API keys are included. See [SETUP.md](SETUP.md) for the full breakdown of
what was intentionally left out.

## Quick start

### Option A0 — just try it first (zero commitment)

Not ready to install anything yet? Copy the template into a scratch temp
directory and open it in Obsidian without touching your real config or
registering anything with Hermes:

```bash
./Scripts/Installers/try.sh        # Linux/macOS
```
```powershell
.\\Scripts\\Installers\\try.ps1        # Windows
```

Delete the scratch copy any time. Run Option A or B below when you're
ready to keep it for real.

### Option A — paste into Hermes (easiest)

If you already run a Hermes agent, skip cloning/scripting entirely: open
**[INSTALL_PROMPT.md](INSTALL_PROMPT.md)** and paste one block straight into
your Hermes chat:

- **Prompt 1** — installs the vault only
- **Prompt 2** — sets up the hourly archiving cron job only (vault must already exist)
- **Prompt 3 (master)** — does both in one paste: install the vault, then set
  up the hourly cron job, no follow-up needed

### Option B — run the installer yourself

`install.sh` / `install.ps1` walk through the same questions interactively.
Real transcript from an actual run:

![install.sh demo transcript](assets/install-demo.png)

**Linux / macOS:**
```bash
git clone https://github.com/mistrysiddh/hermes-brain-template.git
cd hermes-brain-template
chmod +x Scripts/Installers/install.sh
./Scripts/Installers/install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/mistrysiddh/hermes-brain-template.git
cd hermes-brain-template
powershell -ExecutionPolicy Bypass -File .\\Scripts\\Installers\\install.ps1
```

The installer asks a few questions — where to put the vault, which local
embedding backend you want for the optional trend-digest scripts (Ollama or
sentence-transformers), and whether to auto-register the vault path with the
Hermes CLI — then finishes the setup for you.

### Option C — full manual control

Follow **[SETUP.md](SETUP.md)** step by step instead of using either installer.

### Option D — Clone & Use (for developers/contributors)

If you want to work with the template directly or contribute:

```bash
git clone https://github.com/mistrysiddh/hermes-brain-template.git
cd hermes-brain-template
# Open in Obsidian directly, or run installers if needed
obsidian .  # macOS (adjust for your OS)
```

This gives you a clean template vault to customize. For Hermes integration,
run the installer from within the cloned directory:

```bash
./_System/Scripts/Installers/install.sh  # Linux/macOS
.\_System\Scripts\Installers\install.ps1  # Windows
```

Your cloned vault stays update-safe — you can pull template updates later
without losing your local customizations.

## Cross-platform scripts

| Purpose | Windows | Linux/macOS |
|---|---|---|
| Memory consolidation ("dream cycle") | `python _System\Scripts\consolidate_memory.py` | `python3 _System/Scripts/consolidate_memory.py` |
| Skill-to-Chat-Links regeneration | `python _System\Scripts\generate_skill_links.py` | `python3 _System/Scripts/generate_skill_links.py` |
| Trend digest — Ollama backend | `_System\Scripts\pipeline.ps1` | `_System/Scripts/pipeline.sh` |
| Trend digest — sentence-transformers backend | `_System\Scripts\New-TrendDigest.ps1` | `_System/Scripts/trend_digest.sh` |
| **Hourly session archiving + token tracking** | `python _System\Scripts\hourly_archive.py` | `python3 _System/Scripts/hourly_archive.py` |
| **Instant session archiving (manual trigger)** | `python _System\Scripts\archive_now.py` | `python3 _System/Scripts/archive_now.py` |
| **Session enrichment (add summaries)** | `python _System\Scripts\enrich_session.py` | `python3 _System/Scripts/enrich_session.py` |
| **Semantic search index (build/update/serve)** | `python _System\Scripts\semantic_search.py` | `python3 _System/Scripts/semantic_search.py` |
| **Session tagging & topic tracking** | `python _System\Scripts\session_tagger.py` | `python3 _System/Scripts/session_tagger.py` |
| **Future skill forecast** | `python _System\Scripts\skill_forecast.py` | `python3 _System/Scripts/skill_forecast.py` |
| **Vault integrity audit** | `python _System\Scripts\vault_audit.py` | `python3 _System/Scripts/vault_audit.py` |
| **Agent performance dashboard** | `python _System\Scripts\agent_performance.py` | `python3 _System/Scripts/agent_performance.py` |
| **Install / set up vault + cron** | `.\_System\Scripts\Installers\install.ps1` | `./_System/Scripts/Installers/install.sh` |
| **Uninstall / clean up vault** | `.\_System\Scripts\Installers\uninstall.ps1` | `./_System/Scripts/Installers/uninstall.sh` |
| **Update template in existing vault** | `.\_System\Scripts\Installers\update.ps1` | `./_System/Scripts/Installers/update.sh` |
| **Zero-commitment trial run (scratch vault)** | `.\_System\Scripts\Installers\try.ps1` | `./_System/Scripts/Installers/try.sh` |
| Seed sample/demo data (preview only, opt-in) | `python _System\Scripts\seed_sample_data.py .` | `python3 _System/Scripts/seed_sample_data.py .` |

## Requirements

- [Obsidian](https://obsidian.md) (free)
- A [Hermes](https://claude-code.nousresearch.com/docs) agent install (e.g., via [OpenClaw](https://openclaw.nousresearch.com/)), if you want the automated session-archive/memory pipeline
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

## Vault Structure

Here is the organized folder structure of the Hermes Brain template:

```
├── 01-Projects/
│   ├── ADR/
│   │   └── README.md
│   ├── Hermes-Agent-Vault-Setup.md
│   ├── Projects.base
│   └── README.md
├── 02-Areas/
│   ├── README.md
│   ├── Skills/
│   │   ├── Installed-Skills-Index.md
│   │   ├── Lessons-Learned/
│   │   │   └── README.md
│   │   └── Personality-Judgment-Framework.md
│   ├── Team-Profiles-Index.md
│   └── User-Profile.md
├── 03-Resources/
│   ├── README.md
│   ├── Guides/
│   │   ├── Dataview-Query-Library.md
│   │   └── Kanban-Usage.md
│   ├── MOCs/
│   │   ├── AI-ML-MOC.md
│   │   ├── Agentic-Architecture-MOC.md
│   │   ├── Cybersecurity-MOC.md
│   │   └── Technology-Stack-MOC.md
│   └── Research/
│       └── README.md
├── 04-Archives/
│   ├── README.md
│   ├── Daily/
│   │   ├── .gitkeep
│   │   ├── Chat-Correlation.md
│   │   ├── README.md
│   │   └── Timeline.md
│   ├── Memory-Review/
│   │   ├── HERMES-PREAMBLE.md
│   │   ├── Memory-Board.kanban
│   │   └── TEMPLATE.md
│   └── README.md
├── _System/
│   ├── README.md
│   ├── Canvases/
│   │   ├── Dashboard-Beta.md
│   │   ├── Memory-Pipeline.canvas
│   │   └── Personality-Judgment-Canvas.canvas
│   ├── Scripts/
│   │   ├── Installers/
│   │   │   ├── install.ps1
│   │   │   ├── install.sh
│   │   │   ├── try.ps1
│   │   │   ├── try.sh
│   │   │   ├── uninstall.ps1
│   │   │   ├── uninstall.sh
│   │   │   ├── update.ps1
│   │   │   └── update.sh
│   │   ├── agent_performance.py
│   │   ├── archive_now.ps1
│   │   ├── archive_now.py
│   │   ├── build_fixture_vault.py
│   │   ├── consolidate_memory.py
│   │   ├── dream_cycle.py
│   │   ├── enrich_session.ps1
│   │   ├── enrich_session.py
│   │   ├── generate_skill_links.py
│   │   ├── hourly_archive.py
│   │   ├── New-TrendDigest.ps1
│   │   ├── pipeline.ps1
│   │   ├── pipeline.sh
│   │   ├── pull_supermemory.py
│   │   ├── seed_sample_data.py
│   │   ├── semantic_search.py
│   │   ├── session_tagger.py
│   │   ├── skill_forecast.py
│   │   ├── sync_to_hermes.py
│   │   ├── tag_skill_map.json
│   │   ├── trend_digest.py
│   │   └── trend_digest.sh
│   ├── Templates/
│   │   ├── Architecture-Decision-Record.md
│   │   ├── Daily-Review.md
│   │   ├── Lesson-Learned.md
│   │   ├── Personality-Judgment-Analysis.md
│   │   ├── Personality-Judgment-Dashboard.md
│   │   ├── Project.md
│   │   └── Research-Note.md
├── assets/
│   ├── graph-view-screenshot.png
│   └── install-demo.png
├── docs/
│   ├── LICENSE
│   └── CHANGELOG.md
├── .gitignore
├── Dashboard.md
├── INSTALL_PROMPT.md
├── MOC.md
├── README.md
├── SETUP.md
└── Welcome.md
```

**Structure Explanation:**
- **01-Projects/** — Active projects with goals and deadlines
- **02-Areas/** — Long-term standards, skills, and user profile
- **03-Resources/** — Domain knowledge (MOCs, research, guides)
- **04-Archives/** — Historical items (daily sessions, memory review)
- **_System/** — Operational core (templates, scripts, canvases)

This PARA-based structure keeps everything organized and discoverable.

## License

MIT — see [LICENSE](docs/LICENSE). Use, fork, and adapt freely.


## Contributing

Issues and PRs welcome — especially more platform-specific install fixes,
additional Obsidian plugin recipes, or extra automation scripts.
[Discussions](https://github.com/mistrysiddh/hermes-brain-template/discussions)
are enabled if you'd rather ask a question first — start with the
[welcome post](https://github.com/mistrysiddh/hermes-brain-template/discussions/1).
See [CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md) for community guidelines.