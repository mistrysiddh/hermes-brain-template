---
title: Sources — Raw Knowledge Base (Immutable)
type: directory
status: active
---

# Sources — Raw Knowledge Base (Immutable)

This directory holds your curated source documents: articles, papers, PDFs, web clips, meeting transcripts, data files, etc.

**Rule:** Sources are immutable. The LLM reads from them but never modifies them. They are your source of truth.

## Adding a new source

1. Drop the file here (any format: .md, .txt, .pdf, .html, etc.)
2. Tell the LLM agent to ingest it (see `02-Areas/Wiki/` schema)
3. The LLM reads the source, extracts key information, and integrates it into the wiki at `02-Areas/Wiki/`

## Source categories

| Category | Description |
|---|---|
| `03-Resources/Sources/articles/` | Web articles, blog posts, essays |
| `03-Resources/Sources/papers/` | Research papers, academic documents |
| `03-Resources/Sources/meetings/` | Transcripts, call notes, session logs |
| `03-Resources/Sources/data/` | Datasets, exports, raw data files |
| `03-Resources/Sources/other/` | Anything else |

## Retention

Sources live here permanently. The wiki layer references them but never duplicates their full content — it summarizes, extracts, and cross-references.
