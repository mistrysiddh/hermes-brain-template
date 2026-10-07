# Cron Job Metadata

This folder stores metadata, logs, and housekeeping session notes specific to automated cron job runs.

## Contents

- `.hourly_archive.lock` — Cross-process lock file for hourly archiving (prevents concurrent runs)
- `cron-runs.log` — Timestamped log of each cron job execution (success/failure, duration, sessions processed)
- `cron-errors.log` — Errors from cron runs for debugging, also used by `session_git_snapshot.py` to log blocked/failed snapshot attempts
- `git-snapshot.log` — Run history for `session_git_snapshot.py` (one line per session-end snapshot attempt: success, no-op, or blocked)
- `sessions/YYYY/MM/DD/` — The agent session notes for the cron job *itself* (e.g. `cron_<jobid>_<timestamp>-<slug>.md`). These are not your chat sessions — they're the record of the archiving job running — and are kept separate from [[../Daily/README|Daily/]] on purpose (see below).

## Why Separate from Daily/?

The `Daily/` folder contains **your chat session content** (markdown files organized by date) — the actual knowledge.
This `Cron/` folder contains **operational metadata and the cron job's own session record** — the "plumbing" that keeps the pipeline running, not something you're expected to read or link to.

Keeping them separate means:
- `Daily/` stays clean and browsable as a knowledge timeline — no near-empty cron notes inflating Dataview queries or `vault_audit.py`'s orphan count
- Cron debugging is isolated and easy to find
- You can safely ignore/clean `Cron/` without losing real session data

### Upgrading from v1.23.0 or earlier?

v1.23.0 only moved the *lock file and logs* here — cron session notes
themselves kept landing in `Daily/YYYY/MM/DD/` (tracked as
[issue #10](https://github.com/mistrysiddh/hermes-brain-template/issues/10)).
If you're upgrading from that version, run the one-off migration once to move
any existing `cron_*.md` files out of `Daily/` and into `sessions/` here:

```
python _System/Scripts/migrate_cron_sessions.py --vault "<vault-path>" --verbose
```

Safe to re-run — already-migrated files are skipped. New vaults on v1.23.1+
never need this; `hermes_session_sync.py` routes cron sessions here
automatically going forward.
