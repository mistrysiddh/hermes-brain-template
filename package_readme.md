---
title: Package Readme
created: 2026-11-07
type: stub
status: auto-remediated
---

# Hermes Brain Agent Skills

Multi-harness agent skills for the Hermes Brain Obsidian vault template.

## Installation

```bash
pip install hermes-brain-skills
```

Or from GitHub Packages:

```bash
pip install --index-url https://pypi.pkg.github.com/mistrysiddh hermes-brain-skills
```

## Usage

```bash
# List available borg layouts
hermes-brain borg --vault /path/to/vault --layout-list

# Generate education questions
hermes-brain skill-pack --vault /path/to/vault --topic "quantum mechanics"

# Research a paper
hermes-brain paper-mapping --vault /path/to/vault --query "Attention Is All You Need"

# Run self-tests
hermes-brain borg --vault /path/to/vault --test
hermes-brain skill-pack --vault /path/to/vault --test
hermes-brain paper-mapping --vault /path/to/vault --test
```

## Multi-Harness Compliance

All skills accept `--vault <path>`, run in `--dry-run` mode by default, use `--apply` for human-in-the-loop approval, are stdlib-only, and include `--test` self-test suites.

## Skills

| Skill | Description |
|-------|-------------|
| **borg** | Artifact intake, TRUST scanning, ART adapters, S1 Ingestor pipeline |
| **skill-pack** | Education skill packs - questions, self-eval, model routing |
| **paper-mapping** | Paper research via OpenAlex API + Inciteful.XYZ features |

## License

MIT