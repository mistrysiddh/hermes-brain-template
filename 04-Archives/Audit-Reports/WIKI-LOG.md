---
title: Wiki Log — Chronological Record
type: log
status: active
---

# Wiki Log — Chronological Record

Append-only record of wiki activity: ingests, queries, lint passes. Format:

```
## [YYYY-MM-DD] ingest | Source Name
- Action taken
- Pages created/updated

## [YYYY-MM-DD] query | Question summary
- Answer provided
- New page written at ...

## [YYYY-MM-DD] lint | Health check
- Issues found: N
- Issues fixed: N
```

*(empty — first entry will be created by the LLM on first ingest)*
