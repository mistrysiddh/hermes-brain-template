# Changelog

All notable changes to the Hermes Brain vault template. Versions correspond to [GitHub Releases](https://github.com/mistrysiddh/hermes-brain-template/releases).

## [1.5.0] — 2026-09-11
### Added
- **Token usage tracking** — `hourly_archive.py` now extracts prompt/completion tokens from JSONL exports and maintains a running total in `Skills-Notes/Token-Usage.log`. Dashboard shows live token usage (today, all-time, 7-day trend, day-over-day).
- **Token usage trend graph** — Added live SVG line graph visualization of token usage over the last 30 days to Dashboard, showing daily totals with axis labels and data points.
- **Vault integrity audit** — `vault_audit.py` scans for broken wikilinks, stale Memory-Review entries (>30 days), duplicate sessions in manifest, and orphaned files. Writes `Skills-Notes/Vault-Audit-Report.md`. Dashboard shows summary.
- **Agent performance dashboard** — `agent_performance.py` analyzes session archives for skill usage frequency, tool call patterns, daily trends, top sessions by tokens. Writes `Skills-Notes/Agent-Performance.md`. Dashboard shows snapshot.
- Dashboard tiles for all three new features (Token usage, Vault audit, Agent performance) with click-through links.
- `Skills-Notes/Token-Usage.log` starter file.
- Updated `INSTALL_PROMPT.md` with optional weekly cron prompts for vault audit (Sunday 2 AM) and agent performance (Monday 3 AM).
- README script table updated with three new automation scripts.

### Changed
- `hourly_archive.py` — now dual-exports (markdown for vault + JSONL for token extraction), idempotent token logging.
- `INSTALL_PROMPT.md` — added optional weekly cron prompts for vault audit and agent performance.

## [1.4.0] — 2026-09-10
### Added
- Dashboard.md — new "Vault health" section: flags a stale/dead hourly archiver (based on the newest Daily/ session's timestamp) and a growing Memory-Review backlog, both read-only against files already in the vault.
- `Scripts/hourly_archive.py` — exports Hermes sessions from the last hour, reorganizes them into `Daily/YYYY/MM/DD/`, and maintains a deduped `Daily/manifest.jsonl`. Designed to be idempotent — safe to re-run.
- `Scripts/pull_supermemory.py` — pulls all memories for a Supermemory container tag and saves them as both a raw JSON dump and a human-readable markdown note.
- `CHANGELOG.md` and `.github/ISSUE_TEMPLATE/` (bug report + feature request templates, Discussions link).
- `INSTALL_PROMPT.md` — new "Upgrade prompt" section for pulling template updates into an existing vault via a single Hermes paste (wraps `update.sh`/`update.ps1`).
### Changed
- `.gitignore` — added `.smart-env/`.

## [1.3.0] — 2026-09-10
### Added
- In-vault update notifications: `Dashboard.md` now checks GitHub's releases API live and shows a banner if a newer template version is available (fails soft if offline).
- `VERSION` file — tracks the installed template version; carried through fresh installs and future updates.
- `update.sh` / `update.ps1` — safely pull template updates into an already-installed vault via a read-only git remote and 3-way merge, so hand-edited files surface as conflicts instead of being silently overwritten. Personal content (`Daily/`, `Memory-Review/*`, `Projects/*` beyond README, plugin `data.json`) stays protected via the vault's existing `.gitignore`.

## [1.2.0] — 2026-09-10
### Added
- `Dashboard.md` — single landing note with live Dataview views: active projects, open Memory-Review candidates, recent Daily sessions, installed-skills count.
- `Projects/Projects.base` — native Obsidian Bases table view over `Projects/` (all projects grouped by status, active-only filter).
- Bundled Dataview plugin updated to 0.5.70.
### Changed
- README opening rewritten with a punchier hook instead of leading with a feature list; updated hero screenshot.
- Fixed dead links in `MOC.md` to `Skills-Notes/Installed-Skills-Index` and `Team-Profiles-Index`.

## [1.1.0] — 2026-09-08
### Added
- `Scripts/generate_skill_links.py` — generates a Skill-to-Chat-Links index per session.
- `Skills-Notes/Installed-Skills-Index.md` and `Team-Profiles-Index.md` starter tables.
### Fixed
- `Scripts/consolidate_memory.py` — `decided_hashes` was comparing full 40-char hashes against 8-char prefix keys, so already-approved candidates kept reappearing on every run instead of staying excluded.
### Changed
- Consolidated `New-TrendDigest.ps1` and `Write-TrendDigest.ps1` (near-duplicate scripts) into one.

## [1.0.0] — 2026-09-06
### Added
- Initial template release: Obsidian vault structure (Daily/, Memory-Review/, Projects/, Research/, Skills-Notes/), Kanban plugin, 3 note templates (Project, Daily-Review, Research-Note), Dataview query library, `Memory-Pipeline.canvas` visual map.
- Cross-platform installers (`install.sh` / `install.ps1`), `INSTALL_PROMPT.md` for one-paste setup via a Hermes agent.
- CI (bash/python/powershell syntax checks), wiki, MIT license.
