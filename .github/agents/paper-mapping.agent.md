---
name: paper-mapping
description: Paper mapping skill — citation-network discovery via OpenAlex API. Find related papers, citations (papers citing a work), cited-by (papers a work cites), and same-author papers. Writes a dated report to the vault.
tools:
  - repository
---

# paper_mapping.py — Paper Mapping Skill

Paper discovery and citation-network mapping via the OpenAlex API (free, no key required for casual use). Finds related papers, citations, and same-author works for any seed paper.

## What it does

| Subcommand / Flag | What it does |
|-------------------|--------------|
| `--vault <path>` | Scan vault, map paper, write report |
| `--query <title or DOI>` | Paper title or DOI to search for (required) |
| `--per-page <N>` | Number of results per category (default: 10) |
| `--apply` | Write report to vault (default: dry-run) |
| `--test` | Run built-in self-test suite |

## Output

- **Paper Mapping Report** (`04-Archives/Audit-Reports/Paper-Mapping-Report.md`): seed work details, citing works table, cited works table, same-author works table, summary

## Data Sources

| Source | What it provides |
|--------|-----------------|
| OpenAlex API | Paper search, metadata, citations, cited-by, same-author works |
| Inciteful.XYZ | Citation-graph paper discovery (referenced in issue, not yet integrated) |

## Usage

```
@hermes-brain paper-mapping --vault <path> --query "Attention Is All You Need"
@hermes-brain paper-mapping --vault <path> --query "10.48550/arxiv.1706.03762" --per-page 20
@hermes-brain paper-mapping --vault <path> --apply --query "BERT"
```

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
