---
name: auto-remediate
description: Reads Self-Critique-Report.md findings and applies safe auto-fixes — adding --vault CLI args to scripts, adding YAML frontmatter to notes, creating stub notes for broken wikilinks. Human approval required per fix; each applied fix gets its own git commit.
tools:
  - repository
---

# Auto-Remediate Agent

Applies safe fixes from `Self-Critique-Report.md` findings. Each fix is opt-in with human approval; each applied fix gets its own git commit for rollback safety.

## Auto-fixable categories

| Category | What it fixes |
|----------|---------------|
| missing_vault_arg | Adds `--vault` CLI argument to scripts using argparse |
| missing_frontmatter | Adds YAML frontmatter to markdown notes |
| broken_link | Creates stub note placeholders for broken wikilink targets |

## Review-required categories (report only)

| Category | Why human review |
|----------|-----------------|
| module_level_path | Requires refactoring into `init_paths()` |
| hardcoded_path | Requires replacing with `os.path.join(VAULT, ...)` |
| secret_exposure | Never auto-fixed — credentials require manual handling |
| drift | Requires human decision on governance docs |
| stale_cron_file | Human decides archive vs delete |
| orphaned_canvas | Human decides link or archive |

## Usage

```
@hermes-brain auto-remediate --vault <path>
```

Modes:
- `--dry-run` (default): Preview fixes without applying
- `--apply`: Apply safe fixes with per-item approval

Produces `Auto-Remediate-Report.md` in `04-Archives/Audit-Reports/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
