---
name: onboarding
description: Conversational setup for new vault users — profile (name, role, timezone), interests, integrations (GitHub, Discord, Telegram), and vault structure verification. Dry-run default with human-in-the-loop approval.
tools:
  - repository
---

# Onboarding Agent

Guides new users through first-time vault setup with a conversational flow.

## What it collects

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| name | text | Yes | Your name or preferred nickname |
| role | text | Yes | Your role (AI builder, trainer, researcher, sysadmin, etc.) |
| timezone | text | No | Used for scheduling and timestamps |
| interests | list | No | Topics you care about (AI, cybersecurity, Linux, etc.) |
| github_username | text | No | For repo integration and issue linking |
| discord_id | text | No | For Discord notifications |
| telegram_chat_id | text | No | For mobile alerts |
| preferred_editor | text | No | For edit commands |

## What it checks

- Vault PARA structure (01-Projects, 02-Areas, 03-Resources, 04-Archives)
- Existing profile (skips already-answered questions)

## Usage

```
@hermes-brain onboarding --vault <path> setup
@hermes-brain onboarding --vault <path> setup --apply
@hermes-brain onboarding --vault <path> profile
```

Options:
- `--vault` — Vault root path (required)
- `--apply` — Save profile to vault (overrides `--dry-run` default)
- `--save` — Save onboarding report to vault

Saves profile to `04-Archives/Onboarding/user-profile.json` and reports to `04-Archives/Onboarding/`.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
