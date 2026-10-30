---
name: radar
description: Standing surveillance on configured sources (blogs, news feeds, academic papers) → daily/weekly digest. Maintains a sources.jsonl list in the vault, scans RSS/Atom/JSON/arXiv sources, deduplicates items, and writes a dated digest markdown file.
tools:
  - repository
---

# Radar Agent

Standing surveillance skill that tracks configured sources and produces a daily or weekly digest for the Hermes Brain vault.

## What it does

1. **Loads sources** from `04-Archives/Radar/sources.jsonl` (JSONL format)
2. **Scans sources** — RSS/Atom feeds, JSON APIs, arXiv papers
3. **Filters by time window** (default: last 7 days)
4. **Deduplicates** items by stable ID
5. **Generates a digest** markdown file with summary table and per-source details
6. **Writes to vault** at `04-Archives/Radar/digests/Radar-<daily|weekly>-<date>.md`

## Source types

| Type | What it fetches | Example |
|------|----------------|---------|
| rss / atom | Blog/feed RSS or Atom XML | `https://example.com/feed` |
| json | Generic JSON API (GitHub releases, etc.) | `https://api.github.com/repos/.../releases` |
| arxiv | arXiv API query | `cat:cs.AI` |

## Sources file format (JSONL)

```jsonl
{"name": "Hermes Blog", "type": "rss", "url": "https://hermes-agent.nousresearch.com/blog/rss", "category": "news"}
{"name": "arXiv AI", "type": "arxiv", "query": "cat:cs.AI", "category": "papers"}
{"name": "GitHub Releases", "type": "json", "url": "https://api.github.com/repos/mistrysiddh/hermes-brain-template/releases", "category": "news"}
```

## Usage

```
@hermes-brain radar --vault <path> scan --days 7
@hermes-brain radar --vault <path> digest --digest-type daily --days 7
@hermes-brain radar --vault <path> digest --digest-type weekly --days 30 --apply
```

Options:
- `--vault` — Vault root path (required)
- `--sources-file` — Custom sources JSONL path
- `--days N` — Days to look back (default: 7)
- `--digest-type` — daily or weekly (default: daily)
- `--max-per-source N` — Max items per source (default: 20)
- `--dry-run` — Preview digest without writing (default)
- `--apply` — Write digest to vault

Produces `Radar-<type>-<date>.md` in `04-Archives/Radar/digests/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
