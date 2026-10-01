# Feature Skill Packs

This directory contains opt-in skill packs for the Hermes Brain template. Users can copy scripts from these packs into `_System/Scripts/` when they're ready for more advanced features.

## Pack Structure

| Pack | Audience | Contains | Copy Command |
|------|----------|----------|--------------|
| **beginner/** | New users | Core archiving + basic memory promotion | `cp features/beginner/* _System/Scripts/` |
| **analyst/** | Data-curious users | Semantic search, session tagging, dashboard enhancements | `cp features/analyst/* _System/Scripts/` |
| **poweruser/** | Advanced users | All analyst features + skill forecasting, custom canvases | `cp features/poweruser/* _System/Scripts/` |
| **experimental/** | Bleeding-edge | Unstable/alpha scripts (agentic-os integrations, etc.) | `cp features/experimental/* _System/Scripts/` |

## How It Works

1. The template ships with **only `beginner/` scripts** in `_System/Scripts/` by default
2. Users progress by copying feature packs as they grow comfortable
3. Each pack is additive — no conflicts between levels
4. `experimental/` may break between releases (use at your own risk)

## Current Script Assignments

### beginner/ (Core - always available)
- `hourly_archive.py` — Session archiving
- `enrich_session.py` — Session enrichment
- `archive_now.py` — Manual archive trigger
- `promote_memory.py` — Memory promotion (with `--review` mode)
- `consolidate_memory.py` — Memory consolidation

### analyst/ (Adds semantic capabilities)
- `semantic_search.py` — Build/update/serve search index
- `session_tagger.py` — Session tagging & topic tracking
- `agent_performance.py` — Agent performance dashboard
- `trend_digest.py` — Trend digest (sentence-transformers backend)

### poweruser/ (Adds forecasting & customization)
- `skill_forecast.py` — Future skill forecast
- `vault_audit.py` — Vault integrity audit
- `generate_skill_links.py` — Skill-to-chat links regeneration
- `template_drift.py` — Compare vault against template (drift detection)
- Custom canvas templates

### experimental/ (Bleeding edge)
- `build_fixture_vault.py` — Fixture vault builder
- `dream_cycle.py` — Dream cycle consolidation
- `pull_supermemory.py` — Supermemory integration
- `sync_to_hermes.py` — Hermes sync
- Alpha agentic-os integrations

## Usage

```bash
# Start with beginner (already in _System/Scripts/)
# When ready for semantic search:
cp features/analyst/* _System/Scripts/

# When ready for forecasting:
cp features/poweruser/* _System/Scripts/

# For bleeding-edge (use with caution):
cp features/experimental/* _System/Scripts/
```

## Adding New Scripts

1. Place the script in the appropriate pack directory
2. Update this README's table
3. Ensure the installer copies the correct pack based on user selection (future enhancement)
