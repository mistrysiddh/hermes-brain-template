# Hermes Brain Agent Skill Packages

Installable packages for the Hermes Brain multi-harness agent skills. Each package is a standalone zip containing a skill's full source — extract into your vault's `_System/Scripts/` directory and run with `--vault <path>`.

## Available Packages

| Package | Version | Contents | Install into |
|---------|---------|----------|--------------|
| **skill_pack** | v1.53.0 | `skill_pack/` — 10 sub-modules (manager, questions, self_eval, model_router, knowledge_graph, dependency_tree, adaptive_practice, thinking_fields, report, cli) | `_System/Scripts/skill_pack/` |
| **paper_mapping** | v1.54.0 | `paper_mapping/` — 8 sub-modules (http_client, openalex, inciteful, models, mapping, report, cli) | `_System/Scripts/paper_mapping/` |
| **borg** | v1.0.0 | `borg/` — Phase 1 core scaffolding + Phase 2 S1 Ingestor pipeline (layout, models, trust_scanner, art_adapters, cli, pipeline/s1_ingestor) | `_System/Scripts/borg/` |
| **hermes-brain-skills** | v1.0.0 | All three packages combined | `_System/Scripts/` |

## How to Install

1. Download the `.zip` from the [Releases page](https://github.com/mistrysiddh/hermes-brain-template/releases)
2. Extract into your vault root (the zip contains `_System/Scripts/<skill>/` paths)
3. Verify the files landed:
   ```bash
   ls _System/Scripts/skill_pack/cli.py
   ls _System/Scripts/paper_mapping/cli.py
   ls _System/Scripts/borg/cli.py
   ```
4. Run any skill:
   ```bash
   python _System/Scripts/skill_pack/cli.py --vault /path/to/your/vault --test
   python _System/Scripts/paper_mapping/cli.py --vault /path/to/your/vault --test
   python _System/Scripts/borg/cli.py --vault /path/to/your/vault --test
   ```

## Multi-Harness Compliance

Every skill in these packages is multi-harness compliant:
- `--vault <path>` CLI argument (deferred path resolution — no module-level path vars)
- `--dry-run` default mode
- `--apply` for human-in-the-loop approval
- Stdlib-only (no external dependencies)
- `--test` self-test suite

## Release History

| Version | Release | Date |
|---------|---------|------|
| v1.53.0 | Skill Pack decomposition + LearnHarness features | 2026-11-03 |
| v1.54.0 | Paper Mapping: Clean Code decomposition + Inciteful.XYZ features | 2026-11-03 |
| v1.0.0 | Borg: Phase 1 core scaffolding + Phase 2 S1 Ingestor | 2026-11-05 |
| v1.0.0 | Hermes Brain Skills (combined) | 2026-11-05 |

## Using Individual Skills

**Skill Pack (education):**
```bash
python _System/Scripts/skill_pack/cli.py --vault <path> --topic "quantum mechanics"
python _System/Scripts/skill_pack/cli.py --vault <path> --self-eval --answer "Your answer here"
```

**Paper Mapping (research):**
```bash
python _System/Scripts/paper_mapping/cli.py --vault <path> --query "Attention Is All You Need"
python _System/Scripts/paper_mapping/cli.py --vault <path> --apply --query "Attention Is All You Need" --per-page 20
```

**Borg (artifact ingestion):**
```bash
python _System/Scripts/borg/cli.py --vault <path> --layout-list
python _System/Scripts/borg/cli.py --vault <path> --trust-scan --artifact /path/to/file.txt
python _System/Scripts/borg/pipeline/s1_ingestor.py --vault <path> --artifact /path/to/file.txt --test
```

## Contributing

Packages are built from the `_System/Scripts/` directory in the [hermes-brain-template](https://github.com/mistrysiddh/hermes-brain-template) repo. Each release tags the corresponding skill version and attaches the zip as a release asset.