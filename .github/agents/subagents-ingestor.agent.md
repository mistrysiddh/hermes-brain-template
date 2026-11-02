---
name: subagents-ingestor
description: Ingestor sub-agent - scans raw/ directory and ingests new material into the vault with proper categorization (Projects, Areas, Resources, Archives).
tools:
  - repository
---

# Ingestor Sub-Agent

Scans `raw/` directory for new material and ingests it into the appropriate vault directory based on content analysis.

## What it does
- Scans `raw/` directory for new markdown files
- Classifies each note into Projects, Areas, Resources, or Archives based on content
- Writes ingested notes to the appropriate vault directory with proper slugified names

## Usage
```
@hermes-brain subagents/ingestor --vault <path> scan
@hermes-brain subagents/ingestor --vault <path> scan --apply
```

Options:
- `--vault` — Vault root path (required)
- `--apply` — Apply ingestion (overrides --dry-run default)
- `--test` — Run built-in self-test suite

Writes ingested notes to the appropriate vault directory based on content analysis.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
