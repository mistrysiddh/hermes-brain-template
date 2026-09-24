--|
type: skill-reference
status: active
created: 2026-09-23
tags: [skill, reference, hermes-agent, capabilities]
--|

# Hermes Agent Capabilities & Learned Workflows

Reference guide for **what the Hermes Agent can do out-of-the-box** and **practical workflows developed through user interaction**. Focuses on verifiable, practical capabilities — not theory.

> **Fill this in once per major Hermes Agent update.**  
> **Treat it like a living doc: delete sections that don't apply, add your own.**  
> **Goal: < 1 screen — if it's ballooning, details belong in [[01-Projects/README|Projects]] or [[03-Resources/Research/README|Research]] notes.**

--|

## 🔧 Built-In Skills (Out-of-the-Box)
Verified capabilities from `skills_list` — immediately usable in any Hermes Agent session.

| Category          | Skills (Examples)                                                                 | What It Lets You Do                                                                 |
|-------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Core Agent**    | `hermes-agent`, `hermes-platform-configuration`, `hermes-plugin-discovery`       | Configure Hermes itself, manage plugins, inspect system state                     |
| **File System**   | `terminal`, `read_file`, `write_file`, `patch`, `memory`, `search_files`         | Run shell commands, read/edit files, store durable facts, search content          |
| **Version Control**| `github` (via `gh` CLI)                                                         | Clone repos, manage PRs/issues/releases — *used for all template pushes*          |
| **Web**           | `web_search`, `web_extract`                                                     | Search the web, extract page content as markdown — *no API key needed*            |
| **Automation**    | `cronjob_manage`                                                                | Create, list, remove scheduled cron jobs                                          |
| **AI Coding**     | Skills under `autonomous-ai-agents`: `claude-code`, `codex`, `opencode`         | Delegate coding tasks to external AI agents                                       |
| **Tool Management**| `tool_describe`, `tool_call`, `tool_search`                                     | Discover and invoke deferred/local tools                                          |
| **Validation**    | `test-skill`, `verification-loop`                                               | Test skill setups, run verification loops                                         |

**Verification**: Run `skills_list` in any Hermes Agent session to see the full, current list.

--|

## 🧠 Learned Workflows (From User Interaction)
Practical, verified applications of built-in skills — developed to solve *your specific problems*. These live in your vault and template repo as executable patterns.

| Workflow                          | Built-In Skills Used                                                                 | How to Verify/Use                                                                 |
|-----------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Installer Profile Preservation**| `patch`, `terminal`, `github`                                                      | Check `_System/Scripts/Installers/install.sh`/.ps1 for logic that skips `User-Profile.md` copy if destination file exists and has content |
| **CI Lint Workflow Fix**          | `write_file`, `patch`, `terminal`, `github`                                        | See commits [`1d74013`](https://github.com/mistrysiddh/hermes-brain-template/commit/1d74013) and [`1158afa`](https://github.com/mistrysiddh/hermes-brain-template/commit/1158afa) — fixed `vault_audit.py`/`agent_performance.py` paths |
| **Template Release Process**      | `terminal`, `github`                                                               | Standard: `git tag -a vX.Y.Z -m "msg"` → `git push origin vX.Y.Z` → `gh release create` |
| **Vault Profile Population**      | `write_file`, `memory`                                                             | Your actual `02-Areas/User-Profile.md` (10,279 bytes) vs. blank template (9,086 bytes) |
| **Session Sync Verification**     | `terminal`, `read_file`, `write_file`                                              | Check `04-Archives/Daily/` for timestamped session logs — proves sync scripts ran |

**Key insight**: These aren't formal "skills" added via `skill_manage` — they're **reusable, verifiable command sequences** using Hermes Agent's existing capabilities. You can:
- Run them manually (e.g., `./_System/Scripts/vault_audit.py`)
- Add them to cron (e.g., `*/30 * * * * /path/to/vault/_System/Scripts/vault_audit.py`)
- Trigger them via Hermes Agent prompts (e.g., "run the vault audit")

--|

## 📚 Related Files in This Vault
- [[02-Areas/Skills/Installed-Skills-Index|Installed-Skills-Index]] — Index of skills *installed* in this specific vault
- [[02-Areas/Skills/Lessons-Learned/README|Lessons-Learned]] — Practical tips from user-agent interaction
- [[02-Areas/Skills/Skill-to-Chat-Links|Skill-to-Chat-Links]] — Maps skills to chat contexts
- [[02-Areas/Skills/Team-Profiles-Index|Team-Profiles-Index]] — Documents *agent* profiles (not you)
- [[02-Areas/User-Profile|User-Profile]] — **This file** — documents *you*, the human

--|

## 💡 How to Use This Reference
1. **For built-in skills**: Run `skills_list` → pick a skill → run `skill_view(name='skill-name')` for details
2. **For learned workflows**: Look at the referenced files/commits above → copy/paste/adapt the command sequences
3. **To add your own**: Document a verified, repeatable command sequence here — keep it practical and verifiable

> ✅ **Good example**: "Fixed CI lint by making `vault_audit.py` write to resolved VAULT path — see commit 1158afa"  
> ❌ **Not this**: "The agent is now better at linting" (unverifiable, no proof)

--|

See also: [[MOC]] (topic index), [[01-Projects/README|Projects]] (active work), [[03-Resources/Research/README|Research]] (deep dives).