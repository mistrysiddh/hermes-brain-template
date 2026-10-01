# Cron Job Metadata

This folder stores metadata and logs specific to automated cron job runs.

## Contents

- `.hourly_archive.lock` — Cross-process lock file for hourly archiving (prevents concurrent runs)
- `cron-runs.log` — Timestamped log of each cron job execution (success/failure, duration, sessions processed)
- `cron-errors.log` — Errors from cron runs for debugging

## Why Separate from Daily/?

The `Daily/` folder contains **session content** (markdown files organized by date) — the actual knowledge.
This `Cron/` folder contains **operational metadata** — the "plumbing" that keeps the pipeline running.

Keeping them separate means:
- `Daily/` stays clean and browsable as a knowledge timeline
- Cron debugging is isolated and easy to find
- You can safely ignore/clean `Cron/` without losing session data
