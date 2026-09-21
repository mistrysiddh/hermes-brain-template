---
type: skill-note
tags: [kanban, projects, workflow]
---

# Kanban Board Usage — Hermes Brain

This vault ships with [obsidian-kanban](https://github.com/mgmeyers/obsidian-kanban) preconfigured (see `.obsidian/community-plugins.json`). This note covers how to use it inside *this* vault's conventions specifically — the plugin's own docs cover the general UI.

## Creating a board

Right-click any folder in the file explorer → **New Kanban board**. For this vault, the natural place is inside `Projects/` — either one shared board for all active work, or one board per larger project if you prefer granularity.

## Suggested default columns

A simple 4-column layout works well for solo or small-team use with a Hermes agent in the loop:

| Column | Meaning |
|---|---|
| **Backlog** | Captured but not started — ideas, agent suggestions not yet acted on |
| **In Progress** | Actively being worked (by you, or an agent session) |
| **Blocked** | Waiting on a decision, external input, or another card |
| **Done** | Complete — safe to archive off the board periodically |

Create these as the board's list headers (`##` in the underlying markdown) when you first set it up. Add/rename/reorder columns anytime — Kanban boards in this plugin are just markdown files with a specific structure, so nothing is locked in.

## How Kanban cards relate to `Projects/*.md` notes

The vault's `Project.md` template (`_System/Templates/Project.md`) already tracks a project's own `status` frontmatter field (`active`, etc.) and its "Next actions" checklist. The Kanban board is a **different view of the same kind of work**, not a duplicate system — pick one relationship per project and stay consistent:

- **Link, don't duplicate (recommended):** Each Kanban card is a short title that links back to the relevant `01-Projects/*.md` note — e.g. a card titled `[[01-Projects/My-Feature|My-Feature]] — ship v2`. The project note stays the source of truth for goals, decisions, and "why"; the card just tracks where it sits in your workflow *right now*. Moving the card between columns is a status update — you don't need to also update the note's frontmatter every time, unless the note's `status` field matters to a Dataview query elsewhere in the vault.
- **Cards as the whole task (fine for small/one-off items):** For work too small to deserve its own `01-Projects/*.md` note, just write the task directly as a card with no linked note. Promote it to a full project note later if it grows.

Avoid: maintaining full task descriptions in *both* the card text and the project note — that's the duplication this setup is meant to avoid. If a card needs more context than its title, that context belongs in the linked note, not inline in the card.

## Cross-platform notes

`obsidian-kanban` is a pure JS/CSS community plugin (`isDesktopOnly: false` in its manifest) — behavior is identical on Linux, macOS, and Windows. There's no platform-specific setup step; if a board isn't showing card-drag correctly, that's almost always a general Obsidian rendering issue (try toggling Live Preview vs. Source mode), not a Kanban-plugin-specific one. If you hit something that genuinely is platform-specific, please open an issue so this doc can be corrected.

## See also

- [[_System/Templates/Project|Project template]] — the note-side half of this workflow
- [[MOC|MOC]] — vault map of contents
