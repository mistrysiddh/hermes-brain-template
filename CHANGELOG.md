# Changelog

All notable changes to the Hermes Brain vault template. Versions correspond to [GitHub Releases](https://github.com/mistrysiddh/hermes-brain-template/releases).

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
