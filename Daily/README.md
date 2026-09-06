# Daily

Raw session archive, organized `YYYY/MM/DD/<session-file>.md` — one file per Hermes session, exported nightly (redacted) by cron job `7c98ab303154` (`hermes-chat-archive-daily`, 02:00 IST). `manifest.jsonl` in this folder indexes every exported session. Do not silently mutate old files — the exporter only adds new ones.

Also contains **Supermemory imports**: files prefixed `supermemory_<id>-<title>.md`, one per document pulled from the Supermemory API (containerTag `hermes`, 114 docs imported 2026-08-24) and placed under the date it was created. These include both full-session transcripts and explicit memories Supermemory had stored independently — cross-check against local exports before treating as non-duplicate. See [[Supermemory-Session-Index]] for the full list.

This is the raw material for the memory pipeline: review sessions here for durable facts, stage candidates in [[../Memory-Review/TEMPLATE|Memory-Review]], then promote to Hermes's native MEMORY.md/USER.md. See [[../Projects/Hermes-Agent-Vault-Setup]] for the full pipeline diagram, and [[../Skills-Notes/Team-Profiles-Index]] for which agent produced which session.

## Browse chronologically
All 287+ files across every date folder are connected in one browsable, sortable view: [[Timeline]] (live Dataview table — click any row to open that day's folder).
