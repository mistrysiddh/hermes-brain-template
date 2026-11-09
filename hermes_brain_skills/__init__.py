"""Hermes Brain Agent Skills - Multi-harness agent skills for Obsidian vaults.

Available skills:
- borg: Artifact intake/TRUST/ART adapters, record schema, pipeline agents
- skill_pack: Education skill packs - question users, self-evaluate, model routing
- paper_mapping: Paper research via OpenAlex API + Inciteful.XYZ features
- system_one: System One Memory OS — invariants, storage, data model, decision layer

All skills are multi-harness compliant:
- --vault CLI arg, deferred path resolution
- --dry-run default / --apply for human-in-the-loop
- Stdlib-only
- --test self-tests
"""

__version__ = "1.0.0"

from hermes_brain_skills import borg, skill_pack, paper_mapping, system_one

__all__ = ["borg", "skill_pack", "paper_mapping", "system_one", "__version__"]
