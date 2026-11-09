"""Hermes Brain — Skill Pack Manager.

Loads and lists educational skill packs from YAML/JSON files under
<vault>/_System/SkillPacks/.

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - stdlib-only
"""

import json
import os

SKILL_PACK_DIR = "_System/SkillPacks"

# Deferred vault path — resolved at runtime, never at import time
VAULT = None


def init_paths(vault_path):
    """Resolve the vault root path from the given vault path.

    Called from main() before any other operation. Never resolves
    paths at module import time.
    """
    global VAULT
    VAULT = os.path.abspath(vault_path)


def skill_pack_dir(vault):
    """Return the absolute path to the SkillPacks directory under vault."""
    return os.path.join(vault, SKILL_PACK_DIR)


def list_skill_packs(vault):
    """Return dict of skill_pack_name -> pack_data from .json/.yaml files.

    Scans <vault>/_System/SkillPacks/ for .json and .yaml/.yml files.
    JSON is fully supported (stdlib). YAML is parsed only if PyYAML is
    available; otherwise YAML files are skipped silently.
    """
    packs = {}
    spath = skill_pack_dir(vault)
    if not os.path.exists(spath):
        return packs

    for fname in os.listdir(spath):
        fpath = os.path.join(spath, fname)
        if not os.path.isfile(fpath):
            continue

        if fname.endswith(".json"):
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                packs[data.get("name", fname[:-5])] = data
            except Exception:
                continue

        elif fname.endswith((".yaml", ".yml")):
            try:
                import yaml

                with open(fpath, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                packs[data.get("name", fname.rsplit(".", 1)[0])] = data
            except ImportError:
                continue  # yaml not available in stdlib — skip
            except Exception:
                continue

    return packs
