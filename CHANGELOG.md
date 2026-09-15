# Changelog

All notable changes to the Hermes Brain vault template. Versions correspond to [GitHub Releases](https://github.com/mistrysiddh/hermes-brain-template/releases).

## [1.10.0] — 2026-09-14
### Added
- **Activity heatmap** on `Dashboard.md` — a GitHub-style, day-wise calendar heatmap (18 weeks × 7 days) showing token usage intensity per day, reusing the existing `Skills-Notes/Token-Usage.log` data (no new script or cron job needed). Color intensity scales toward the active theme's accent color via 4 steps, so it matches whichever theme (Nemoclaw, Tokyo Night, etc.) is active. Hover any cell for the exact date, tokens, and session count. Built with plain colored `<div>` cells (not SVG) to avoid the Dataview parser fragility that broke the earlier token-trend graph in v1.5.1–v1.5.3.
- **`Scripts/seed_sample_data.py`** — opt-in sample/demo data generator (not shipped pre-populated, addresses the "empty vault on first open" problem from issue discussion around #9 without the staleness risk of committing fake data by default). Run it yourself to populate `Daily/`, `Memory-Review/`, `Projects/`, and `Skills-Notes/Token-Usage.log` with realistic-looking fake sessions/candidates/a project note, so a freshly installed vault's Dashboard and graph view show a populated state instead of empty. Every generated file/entry is tagged `sample: true` (or `[sample]` in the token log) for easy removal later.

## [1.9.1] — 2026-09-14
### Changed
- **`INSTALL_PROMPT.md` — all 4 cron-job creation prompts now check before creating.** Previously the wording only asked the agent to check for a *conflicting* archiving job before creating the hourly archiver; it didn't explicitly tell it to skip creation if a job with the *same name* already existed for any of the 4 cron prompts (hourly archive, weekly vault audit, weekly agent performance, and the combined master install+cron prompt). Each now explicitly instructs: call `cronjob_manage(action='list')` first, and if a job with that name (or targeting the same vault Daily/ folder) already exists, don't create a duplicate — just report that it's already set up.

## [1.9.0] — 2026-09-14
### Added
- **Light-mode variant of the Nemoclaw theme** (fixes #2) — added a full `.theme-light` block to `.obsidian/themes/Nemoclaw/theme.css` (all CSS variables + structural touches mirrored from the existing `.theme-dark` block, same NVIDIA-green accent darkened for AA contrast on white surfaces). Switch via Settings → Appearance → Base color scheme → Light while Nemoclaw is active. Theme manifest bumped to 1.1.0.
- **`Skills-Notes/Kanban-Usage.md`** (fixes #3) — new doc covering suggested default columns (Backlog/In Progress/Blocked/Done), how Kanban cards relate to `Projects/*.md` notes (link-don't-duplicate pattern), and cross-platform behavior notes for the bundled `obsidian-kanban` plugin. Linked from `MOC.md`.

## [1.8.0] — 2026-09-14
### Added
- **OpenClaw badge** in README, alongside the existing Hermes badge.

### Fixed
- **`update.sh` / `update.ps1` merge conflicts on `User-Profile.md`** (fixes #5) — a user who fills in `User-Profile.md` before or independently of a template update could hit a hard "both-added" git merge conflict on every future `update.sh` run, since the template also ships its own (blank) copy of the same filename. Both update scripts now register a local-only `merge=ours` git attribute for `User-Profile.md` on every run: the first pull still delivers the blank scaffold to new vaults as normal, but every pull after that silently keeps the user's local content on conflict instead of stopping with conflict markers. This is vault-local config (`.git/info/attributes`), never synced to the template repo itself.
- Conflict-resolution tip added to both update scripts' failure output, and a new "Resolving update.sh/update.ps1 merge conflicts" section in `CONTRIBUTING.md`, covering the remaining conflict class (customized `.obsidian/appearance.json` / theme `theme.css`) that the merge driver doesn't cover.

## [1.7.1] — 2026-09-14
### Fixed
- **Personal Data Guard workflow** — the v1.7.0 release's guard job failed on push because its allow-list was missing `Daily/Timeline.md`, `Daily/Chat-Correlation.md`, and `Daily/.gitkeep`, and its empty-tree fallback re-flagged every pre-existing template file as "new" whenever `github.event.before` was the null SHA. Completed the allow-list and changed the fallback to diff against the last commit instead of the empty tree.

## [1.7.0] — 2026-09-14
### Added
- **`try.sh` / `try.ps1`** — copy the template into a scratch temp directory and open it in Obsidian with zero commitment: no Hermes CLI registration, no cron setup, doesn't touch your real Obsidian config. Delete the copy any time.
- **`uninstall.sh` / `uninstall.ps1`** — cleanly remove a vault installation: unsets `env.HERMES_VAULT_PATH` if it points at the target vault, warns about any Hermes cron job that may still reference it, and optionally deletes the vault directory after a typed confirmation.
- **CI: Personal Data Guard** (`.github/workflows/personal-data-guard.yml`) — new workflow that fails a push/PR if it touches disallowed personal-content paths (`Daily/`, `Memory-Review/`, `Research/`, `.smart-env/`, plugin `data.json` files) outside the template's own allowed exceptions (`Memory-Review/TEMPLATE.md`, `Daily/README.md`, `Research/README.md`). Automates what `CONTRIBUTING.md` previously only asked contributors to self-check.
- **CI: `consolidate_memory.py` content-correctness tests** (`Scripts/ci/test_consolidate_memory.py`) — 6 tests asserting on actual output content (not just "did a file get written"): exact-duplicate dedup, fuzzy near-duplicate dedup, secret-string scrubbing, false-positive check on normal facts, decided-candidate exclusion (regression test for the v1.1.0 hash-prefix bug), and state-file JSON validity.
- **CI: extended runtime smoke-test** — `generate_skill_links.py` now also runs against the fixture vault in the `runtime-smoke-test` job (alongside the existing `vault_audit.py`, `agent_performance.py`, `hourly_archive.py` coverage). `pull_supermemory.py` and `trend_digest.py` are intentionally excluded — the former needs a real/mocked network API + key, the latter needs `sentence-transformers`, a heavy ML dependency not worth adding to this lint job.
- **CI badge** in README, linking to the Lint Scripts Actions workflow.

### Changed
- `CONTRIBUTING.md` — notes that the Personal Data Guard CI job now automatically enforces the "never commit real vault content" rule, not just an honor-system reminder.

## [1.6.0] — 2026-09-11
### Added
- **User-Profile.md** — new template note documenting the human user's identity, communication preferences, technical environment, standing facts, current focus, interests, and boundaries for the agent. Includes a distinctive "What the agent has noticed about you" section, written by the agent (not the user) based on real interaction patterns — a mirror, not a form.
- **Nemoclaw theme** — new custom dark theme bundled in `.obsidian/themes/Nemoclaw/`, NVIDIA-inspired black background with signature green (#76b900) accents, monospace headings, and a subtle grid overlay. Now the template's default theme (was Tokyo Night, still available as an alternative via Settings → Appearance).
- MOC.md and Dashboard.md link to User-Profile.md for discoverability.

## [1.5.3] — 2026-09-11
### Removed
- **Token usage trend graph** — Removed the live SVG line graph visualization of token usage from Dashboard.md to simplify the token usage section.

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
