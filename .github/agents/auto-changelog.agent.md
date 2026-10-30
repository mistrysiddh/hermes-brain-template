---
name: auto-changelog
description: CI/CD changelog generator from conventional commits. Scans git history, parses feat/fix/docs/etc. commits, groups them by type, and writes a dated Keep-a-Changelog-style markdown file. Reports only — never auto-commits.
tools:
  - repository
---

# Auto-Changelog Agent

Generates a dated changelog from git commit history using conventional commit parsing.

## What it does

| Feature | What it does |
|---------|-------------|
| Conventional commit parsing | Parses feat/fix/docs/refactor/perf/test/build/ci/chore/sec commits |
| Type grouping | Groups commits into Features, Bug Fixes, Documentation, etc. |
| Unreleased section | Shows commits since the last tag |
| Released sections | Lists the last 10 tagged releases |
| Commit links | Links each entry to its GitHub commit SHA |

## Output format

Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

```
## [Unreleased]

### Features

- add login endpoint (auth) 💥 ([abc123d](.../commit/abc123d))

### Bug Fixes

- fix parser crash ([def456e](.../commit/def456e))
```

## Usage

```
@hermes-brain auto-changelog --vault <path> generate --since v1.29.0
@hermes-brain auto-changelog --vault <path> generate --apply
```

Options:
- `--vault` — Vault root path (required)
- `--since` — Git ref to start from (default: latest tag)
- `--output` — Custom output file path
- `--dry-run` — Preview changelog without writing (default)
- `--apply` — Write changelog to vault

Writes to `04-Archives/Metrics/changelog/Changelog-<date>.md`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
