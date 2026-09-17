# Daily

Raw session archive, organized `YYYY/MM/DD/<session-file>.md` — one file per
Hermes session, exported by your archiving cron job (or manual trigger). 
`manifest.jsonl` (once your cron job creates it) indexes every exported session. 
Don't silently mutate old files — the exporter should only add new ones.

## Auto-archiving options

You have **two complementary ways** to get sessions from Hermes into your vault:

- **Hourly cron (passive, default)** – `Scripts/hourly_archive.py` (or `.ps1`) runs once per hour, exporting anything active in the last ~70 minutes. This is what the standard update/install process sets up for you. Expect up to ~70 minutes latency before a session appears in the vault.  
- **Instant archive (manual, on-demand)** – `Scripts/archive_now.py` (or `.ps1`) exports sessions *right now* from a configurable window (default: last 5 minutes). Run it whenever you finish a long chat session and want the transcript available immediately. Both scripts use the same lock file (`.hourly_archive.lock`) so they can never run at the same time and corrupt `manifest.jsonl`.

**Optional session enrichment** – After archiving (either hourly or instant), you can run `Scripts/enrich_session.py` (or `.ps1`) to add a simple summary frontmatter to session markdown files that don't already have one. This makes sessions more glanceable and provides seed data for future memory pipeline steps.

Both archiving scripts:
- Export redacted markdown + JSONL (for token usage)
- Reorganize files into `Daily/YYYY/MM/DD/`
- Update the deduplicated `manifest.jsonl`
- Append to `Skills-Notes/Token-Usage.log`

This is the raw material for the memory pipeline: review sessions here for
durable facts, stage candidates in [[../Memory-Review/TEMPLATE|Memory-Review]],
then promote to Hermes's native MEMORY.md/USER.md. See
[[../Projects/README]] for project context and the pipeline overview, and
[[../Memory-Pipeline.canvas|Memory-Pipeline]] for a visual map.

## Browse chronologically

Once sessions start landing here, [[Timeline]] gives a live, sortable
Dataview table across every date folder — no more clicking through
`YYYY/MM/DD/` one at a time. [[Chat-Correlation]] breaks archived chats down
by source pattern and (optionally) by agent profile.