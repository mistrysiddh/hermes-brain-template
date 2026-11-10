"""Hermes Brain — Skill Pack Dependency Tree / Lesson Map.

Builds a minimal dependency map from current understanding to a
learning goal, rendered as a Mermaid-subset DAG (lesson map).

Inspired by LearnHarness's Plan phase:
- Dependency tree generation — minimal dependency map from current
  understanding to goal.
- Lesson map visualization — dependency map rendered as a visual map.
- Adaptive replanning — lesson adapts when understanding differs
  from the initial probe.
- Author-once plan tree — schema-validated plan_init, DAG validated.

Multi-harness compliant: stdlib-only, --dry-run default, --apply.
"""

from typing import Any

# Deferred vault path — resolved at runtime
VAULT = None


def init_paths(vault_path):
    """Resolve the vault root path from the given vault path."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


import os  # noqa: E402  (import after VAULT declaration for clarity)


def build_dependency_tree(
    goal: str,
    current_understanding: list[str],
    dependencies: dict[str, list[str]] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a minimal dependency map from current understanding to goal.

    Args:
        goal: The learning goal (e.g., "understand quantum entanglement").
        current_understanding: Concepts the learner already understands.
        dependencies: Optional map of concept → list of prerequisite
            concepts. If None, a minimal synthetic dependency graph is
            built from the goal words.
        dry_run: If True, the tree is returned but not written.

    Returns:
        {
            "goal": str,
            "root": str,
            "nodes": list[str],
            "edges": list[tuple[str, str]],
            "mermaid": str,      # Mermaid graph TD definition
            "dag_valid": bool,
            "dry_run": bool,
        }

    """
    if dependencies is None:
        # Minimal synthetic: goal depends on its key words, which depend
        # on anything in current_understanding (already satisfied).
        deps: dict[str, list[str]] = {goal: list(current_understanding)}
    else:
        deps = dependencies

    nodes = set()
    edges: list[tuple[str, str]] = []

    for concept, prereqs in deps.items():
        nodes.add(concept)
        for prereq in prereqs:
            nodes.add(prereq)
            edges.append((prereq, concept))  # prereq -> concept

    # Ensure current understanding concepts are nodes too
    for c in current_understanding:
        nodes.add(c)

    # DAG validation: no node should depend on itself (directly or
    # indirectly). Simple check: no self-loops.
    dag_valid = not any(a == b for a, b in edges)

    # Build Mermaid graph TD
    lines = ["graph TD"]
    for node in sorted(nodes):
        safe = node.replace(" ", "_").replace("-", "_")
        lines.append(f'    {safe}["{node}"]')
    for src, dst in edges:
        safe_src = src.replace(" ", "_").replace("-", "_")
        safe_dst = dst.replace(" ", "_").replace("-", "_")
        lines.append(f"    {safe_src} --> {safe_dst}")
    mermaid = "\n".join(lines)

    tree = {
        "goal": goal,
        "root": goal,
        "nodes": sorted(nodes),
        "edges": [list(e) for e in edges],
        "mermaid": mermaid,
        "dag_valid": dag_valid,
        "dry_run": dry_run,
    }

    if not dry_run and VAULT:
        _save_tree(VAULT, tree)

    return tree


def _save_tree(vault, tree: dict[str, Any]):
    """Persist a dependency tree to the vault."""
    d = os.path.join(vault, "_System", "SkillPacks", "dependency_trees")
    os.makedirs(d, exist_ok=True)
    safe_goal = tree["goal"].replace(" ", "_")[:40]
    path = os.path.join(d, f"{safe_goal}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)


def list_dependency_trees(vault) -> list[dict[str, Any]]:
    """List all saved dependency trees from the vault."""
    d = os.path.join(vault, "_System", "SkillPacks", "dependency_trees")
    if not os.path.exists(d):
        return []
    trees = []
    for fname in os.listdir(d):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, fname), encoding="utf-8") as f:
                trees.append(json.load(f))
        except Exception:
            continue
    return trees
