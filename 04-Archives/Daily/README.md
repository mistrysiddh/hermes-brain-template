# Daily

Raw session archive, organized `YYYY/MM/DD/<session-file>.md` — one file per
Hermes session, exported automatically by Hermes lifecycle hooks, your archiving cron job, or manual trigger. 
`manifest.jsonl` indexes every exported session and keeps track of message counts and export timestamps.
When an existing chat session is continued, its archive file is automatically updated in-place with all new turns.

## Auto-archiving options

You have **three complementary ways** to get sessions from Hermes into your vault:

- **Real-time lifecycle hooks (instant, automatic)** – Configured in `~/.hermes/config.yaml` (`on_session_start`, `post_llm_call`, `on_session_end`). A new Markdown file is immediately created when a new chat starts, and updated after every turn when chatting in an ongoing or older session.
- **Hourly cron (passive background sync)** – `_System/Scripts/hourly_archive.py` (or `.ps1`) runs once per hour, exporting anything active in the last ~70 minutes. Uses database-aware inspection of Hermes `state.db` so even active, non-finalized sessions are caught.
- **Instant archive (manual, on-demand)** – `_System/Scripts/archive_now.py` (or `.ps1`) exports sessions *right now* from a configurable window (default: last 5 minutes) or for a specific `--session-id`.

All archiving triggers:
- Export redacted markdown + JSONL (for token usage)
- Reorganize files into `04-Archives/Daily/YYYY/MM/DD/`
- Clean up any temporary or placeholder slugs when titles are auto-generated
- Update the deduplicated `manifest.jsonl`
- Append to `04-Archives/Audit-Reports/Token-Usage.log`
- Use the shared `.hourly_archive.lock` file so concurrent executions never conflict

**Optional session enrichment** – After archiving, you can run `_System/Scripts/enrich_session.py` (or `.ps1`) to add a simple summary frontmatter to session markdown files that don't already have one.

This is the raw material for the memory pipeline: review sessions here for
durable facts, stage candidates in [[../Memory-Review/TEMPLATE|Memory-Review]],
then promote to Hermes's native MEMORY.md/USER.md. See
[[../../01-Projects/README]] for project context and the pipeline overview, and
[[../../Canvases/Memory-Pipeline.canvas|Memory-Pipeline]] for a visual map.

## Browse chronologically

Once sessions start landing here, [[Timeline]] gives a live, sortable
Dataview table across every date folder — no more clicking through
`YYYY/MM/DD/` one at a time. [[Chat-Correlation]] breaks archived chats down
by source pattern and (optionally) by agent profile.