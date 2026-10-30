---
name: self-critique
description: Audits the Hermes Brain vault and scripts for issues — broken wikilinks, missing frontmatter, module-level path resolution, hardcoded paths, secret exposure, session residue, and Decision/Principle/Axiom drift. Runs in dry-run mode by default; use --apply to fix issues.
tools:
  - repository
---

# Self-Critique Agent

Audits the Hermes Brain vault and its agent scripts for structural issues.

## What it checks

- **Vault health**: Broken wikilinks, missing frontmatter, Decision/Principle/Axiom drift
- **Script hygiene**: Module-level path resolution, hardcoded vault paths, missing `--vault` CLI arg
- **Session residue**: Stale cron files (>90 days), orphaned canvases
- **Security**: Secret/credential exposure in plaintext (API keys, tokens, SSH keys, private keys, JWTs)

## Categories

| Category | Severity | Auto-fixable? |
|----------|----------|---------------|
| critical | secret_exposure | No (human review required) |
| high | module_level_path | No (manual refactor needed) |
| medium | broken_link, hardcoded_path, missing_frontmatter | Yes |
| low | stale_cron_file, orphaned_canvas | No (human decision) |
| info | drift | No (human decision) |

## Usage

```
@hermes-brain self-critique --vault <path>
```

Runs in dry-run mode by default. Pass `--apply` to apply safe fixes (missing_vault_arg, missing_frontmatter, broken_link).

## Example

```
@hermes-brain self-critique --vault /path/to/vault all
```

Produces a `Self-Critique-Report.md` in `04-Archives/Audit-Reports/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
