"""Hermes Brain — Borg Repo Layout (§19.1).

Creates and manages the borg catalog directory structure:

```
roles/ skills/ fundamentals/ orchestrations/ triggers/ policies/ tools/
resources/{references,templates,examples,scripts,memory,glossaries,tests}/
nuances/ advice/ decision-cards/ analogies/ variants/{golden,slm,domain}/
incubating/ quarantine/ rejected/ proposals/ adapters/{harness-versions}/
adrs/{forward,reverse,meta,advice,tie-breaker}/
evals/ probes/{skid,knowledge,parallel,ab,guardrail}/
indexes/ traces/ web-enrichments/
registry.yaml categories.yaml redirects.yaml model-envelopes.yaml CODEOWNERS
"""

import os
from typing import Any

# Deferred vault path — resolved at runtime
VAULT = None

BORG_DIR = "borg"

# Top-level directories
TOP_DIRS = [
    "roles",
    "skills",
    "fundamentals",
    "orchestrations",
    "triggers",
    "policies",
    "tools",
    "nuances",
    "advice",
    "decision-cards",
    "analogies",
    "incubating",
    "quarantine",
    "rejected",
    "proposals",
    "adrs",
    "evals",
    "indexes",
    "traces",
    "web-enrichments",
]

# Nested directories
NESTED_DIRS = {
    "resources": ["references", "templates", "examples", "scripts", "memory", "glossaries", "tests"],
    "variants": ["golden", "slm", "domain"],
    "adapters": ["harness-versions"],
    "adrs": ["forward", "reverse", "meta", "advice", "tie-breaker"],
    "probes": ["skid", "knowledge", "parallel", "ab", "guardrail"],
}

# Root-level files
ROOT_FILES = [
    "registry.yaml",
    "categories.yaml",
    "redirects.yaml",
    "model-envelopes.yaml",
    "CODEOWNERS",
]


def init_paths(vault_path: str) -> None:
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


def borg_dir(vault: str | None = None) -> str:
    """Return the absolute path to the borg catalog directory."""
    v = vault or VAULT
    if not v:
        raise ValueError("Vault path not initialized — call init_paths() first")
    return os.path.join(v, BORG_DIR)


def create_layout(vault: str | None = None, dry_run: bool = True) -> dict[str, Any]:
    """Create the full borg repo layout under <vault>/borg/.

    Returns a dict with 'created' (list of paths) and 'errors' (list).
    """
    v = vault or VAULT
    if not v:
        raise ValueError("Vault path not initialized — call init_paths() first")

    root = borg_dir(v)
    created: list[str] = []
    errors: list[str] = []

    def mkdir(path: str) -> None:
        if dry_run:
            created.append(path)
        else:
            try:
                os.makedirs(path, exist_ok=True)
                created.append(path)
            except OSError as e:
                errors.append(f"{path}: {e}")

    # Top-level directories
    for d in TOP_DIRS:
        mkdir(os.path.join(root, d))

    # Nested directories
    for parent, children in NESTED_DIRS.items():
        for child in children:
            mkdir(os.path.join(root, parent, child))

    # Variants sub-nested
    for variant in NESTED_DIRS["variants"]:
        mkdir(os.path.join(root, "variants", variant))

    # Adapters harness-versions
    mkdir(os.path.join(root, "adapters", "harness-versions"))

    # ADRs sub-nested
    for adr_type in NESTED_DIRS["adrs"]:
        mkdir(os.path.join(root, "adrs", adr_type))

    # Probes sub-nested
    for probe in NESTED_DIRS["probes"]:
        mkdir(os.path.join(root, "probes", probe))

    # Root-level files (empty stubs)
    for fname in ROOT_FILES:
        path = os.path.join(root, fname)
        if dry_run:
            created.append(path)
        else:
            try:
                if not os.path.exists(path):
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("# Borg catalog — auto-generated\n")
                    created.append(path)
            except OSError as e:
                errors.append(f"{path}: {e}")

    return {"created": created, "errors": errors, "dry_run": dry_run, "root": root}


def list_layout(vault: str | None = None) -> dict[str, Any]:
    """List the current borg layout (what exists on disk)."""
    v = vault or VAULT
    if not v:
        raise ValueError("Vault path not initialized — call init_paths() first")

    root = borg_dir(v)
    if not os.path.exists(root):
        return {"exists": False, "root": root, "dirs": [], "files": []}

    dirs: list[str] = []
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel != ".":
            dirs.append(rel)
        for fn in filenames:
            files.append(os.path.relpath(os.path.join(dirpath, fn), root))

    return {"exists": True, "root": root, "dirs": sorted(dirs), "files": sorted(files)}
