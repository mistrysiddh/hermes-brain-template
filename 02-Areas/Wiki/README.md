---
title: Wiki — LLM-Maintained Knowledge Base
type: directory
status: active
---

# Wiki — LLM-Maintained Knowledge Base

This directory is the **wiki layer** of your Hermes Brain vault. It is maintained entirely by your AI agent (you read it, the LLM writes it). It contains structured, interlinked Markdown files: summaries, entity pages, concept pages, comparisons, and a synthesis.

## How it works

1. **You** add sources to `03-Resources/Sources/` and tell the LLM to ingest them
2. **The LLM** reads each source, extracts key information, and writes/updates wiki pages here
3. **You** read the wiki, follow links, check the graph view — the wiki is your IDE, the LLM is the programmer
4. **Periodically** the LLM lints the wiki for contradictions, orphan pages, and missing cross-references

## Page types

| Type | Description | Example |
|---|---|---|
| `entities/` | People, companies, products, tools | `entities/karpathy.md` |
| `concepts/` | Ideas, techniques, patterns | `concepts/llm-wiki.md` |
| `comparisons/` | Head-to-head comparisons | `comparisons/obsidian-vs-notion.md` |
| `sources/` | Summaries of ingested sources | `sources/slopless-slopless.md` |
| `synthesis/` | Cross-cutting analyses | `synthesis/knowledge-management-strategy.md` |

## Key files

- `index.md` — Catalog of all wiki pages with links and summaries
- `../04-Archives/Audit-Reports/WIKI-LOG.md` — Chronological record of ingests, queries, lint passes

## Using Obsidian

Open this vault in Obsidian and use:
- **Graph view** — See the shape of your wiki: what's connected to what, hubs vs orphans
- **Dataview** — Query pages by YAML frontmatter (tags, dates, source counts)
- **Kanban** — Track ingestion pipeline (to-read → ingesting → wiki-updated)

## Schema

The LLM follows `_System/Templates/WIKI-SCHEMA.md` — read it to understand the conventions, workflows, and page formats.
