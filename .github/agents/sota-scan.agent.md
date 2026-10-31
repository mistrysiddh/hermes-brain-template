---
name: sota-scan
description: Benchmark this repo against state-of-the-art projects in the same domain — scans comparators, clusters into peer groups, builds a capability matrix, and ranks gaps as an actionable to-do list.
tools:
  - repository
---

# SOTA Scan Agent

Benchmarks the Hermes Brain vault against top projects in the same domain:
- Scans comparator repos via GitHub API
- Clusters them into peer groups by methodology
- Classifies this repo into its closest cluster
- Builds a capability matrix: Us vs SOTA vs Gap vs Reference
- Ranks gaps as an actionable to-do list (table-stakes first)
- Persists results to `.sota/` directory for progress tracking

Based on https://github.com/MerlijnW70/sota-scan

## Scan Modes

| Mode | Comparators | Best for |
|------|-------------|----------|
| quick | 3-5 | Fast ballpark check |
| standard | 5-10 | Everyday use (default) |
| exhaustive | 10+ | Launch / investor readiness |

## Usage

```
@hermes-brain sota-scan --vault <path> scan --domain "agent-brain-vault" --count 8
@hermes-brain sota-scan --vault <path> scan --save
```

Options:
- `--vault` — Vault root path (required)
- `--domain` — Domain to benchmark against (default: agent-brain-vault)
- `--count` — Max comparators to fetch (default: 8)
- `--save` — Save scan artifacts to vault
- `--dry-run` — Preview report without writing (default)
- `--apply` — Write artifacts to vault

Writes to `.sota/last-scan.json` and `.sota/rubric.<domain>.json`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
