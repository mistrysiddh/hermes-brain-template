# Daily

Raw session archive, organized `YYYY/MM/DD/<session-file>.md` — one file per
Hermes session, exported by your archiving cron job. `manifest.jsonl` (once
your cron job creates it) indexes every exported session. Don't silently
mutate old files — the exporter should only add new ones.

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
