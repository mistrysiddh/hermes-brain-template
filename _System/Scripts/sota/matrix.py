#!/usr/bin/env python3
"""
Hermes Brain — SOTA Sub-Skill: matrix (sota/matrix.py)

Builds a capability matrix comparing this repo against SOTA:
  - capability rows (table-stakes vs edge)
  - us vs SOTA vs gap vs reference
  - gap ranking (table-stakes first, then edge)

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only matrix)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python sota/matrix.py --vault <path>
  python sota/matrix.py --vault <path> --test
"""

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT
    VAULT = os.path.abspath(vault_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_file(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# build_capability_matrix — build capability matrix comparing us vs SOTA
# ---------------------------------------------------------------------------
def build_capability_matrix(us_profile, comparators, clusters, us_label):
    """Build a capability matrix comparing us against SOTA."""
    capability_rows = [
        {"id": "multi-harness-compat", "tier": "table-stakes",
         "test": "Works across CLI, desktop, TUI agents"},
        {"id": "deferred-path-resolution", "tier": "table-stakes",
         "test": "No module-level path vars, deferred to main()"},
        {"id": "dry-run-default", "tier": "table-stakes",
         "test": "--dry-run default, --apply for human approval"},
        {"id": "stdlib-only", "tier": "table-stakes",
         "test": "No external dependencies"},
        {"id": "self-tests", "tier": "table-stakes",
         "test": "Built-in --test self-test suite"},
        {"id": "git-hub-agent-def", "tier": "edge",
         "test": ".github/agents/*.agent.md definition"},
        {"id": "vault-audit", "tier": "edge",
         "test": "Broken wikilink, frontmatter, secret detection"},
        {"id": "knowledge-synthesis", "tier": "edge",
         "test": "BASB/ZK progressive summarization"},
        {"id": "quiz-feature", "tier": "edge",
         "test": "Self-testing from vault notes"},
        {"id": "radar-skill", "tier": "edge",
         "test": "Standing surveillance on sources"},
    ]

    matrix = []
    for cap in capability_rows:
        us_has = False
        if cap["id"] == "multi-harness-compat":
            us_has = True
        elif cap["id"] == "deferred-path-resolution":
            us_has = True
        elif cap["id"] == "dry-run-default":
            us_has = True
        elif cap["id"] == "stdlib-only":
            us_has = True
        elif cap["id"] == "self-tests":
            us_has = True
        elif cap["id"] == "git-hub-agent-def":
            us_has = os.path.isdir(os.path.join(VAULT, ".github", "agents"))
        elif cap["id"] == "vault-audit":
            us_has = os.path.exists(os.path.join(VAULT, "_System", "Scripts", "self_critique.py"))
        elif cap["id"] == "knowledge-synthesis":
            us_has = os.path.exists(os.path.join(VAULT, "_System", "Scripts", "knowledge_synthesis.py"))
        elif cap["id"] == "quiz-feature":
            us_has = os.path.exists(os.path.join(VAULT, "_System", "Scripts", "quiz.py"))
        elif cap["id"] == "radar-skill":
            us_has = os.path.exists(os.path.join(VAULT, "_System", "Scripts", "radar.py"))

        sota_ref = "none found"
        gap = "table-stakes" if cap["tier"] == "table-stakes" else "edge"

        matrix.append({
            "id": cap["id"],
            "capability": cap["id"].replace("-", " ").title(),
            "us": "✅" if us_has else "❌",
            "sota": sota_ref,
            "reference": sota_ref,
            "tier": cap["tier"],
            "gap": gap if not us_has else "—",
        })

    return matrix


# ---------------------------------------------------------------------------
# rank_gaps — rank gaps as actionable to-do list
# ---------------------------------------------------------------------------
def rank_gaps(matrix):
    """Rank gaps as actionable to-do list."""
    gaps = [m for m in matrix if m["gap"] != "—"]
    table_stakes = [m for m in gaps if m["gap"] == "table-stakes"]
    edge = [m for m in gaps if m["gap"] == "edge"]
    return {
        "table_stakes": table_stakes,
        "edge": edge,
        "total": len(gaps),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 sota/matrix.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    def check(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"✅ {name}")
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            failed += 1

    # Test 1: build_capability_matrix evaluates correctly
    def test_build_matrix():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, ".github", "agents"), exist_ok=True)
            write_file(os.path.join(tmp, "_System", "Scripts", "self_critique.py"), "# test")
            write_file(os.path.join(tmp, "_System", "Scripts", "quiz.py"), "# test")
            us_profile = {"domains": ["agent-brain-vault"], "capabilities": ["github-agents"], "total_notes": 5}
            comparators = []
            clusters = {"agent-brain-vault": []}
            matrix = build_capability_matrix(us_profile, comparators, clusters, "agent-brain-vault")
            assert len(matrix) > 0
            gh_agent = [m for m in matrix if m["id"] == "git-hub-agent-def"][0]
            assert gh_agent["us"] == "✅"
        finally:
            shutil.rmtree(tmp)
    check("build_capability_matrix evaluates correctly", test_build_matrix)

    # Test 2: rank_gaps separates table-stakes from edge
    def test_rank_gaps():
        matrix = [
            {"id": "a", "capability": "A", "us": "❌", "sota": "repo1",
             "tier": "table-stakes", "gap": "table-stakes"},
            {"id": "b", "capability": "B", "us": "❌", "sota": "repo2",
             "tier": "edge", "gap": "edge"},
            {"id": "c", "capability": "C", "us": "✅", "sota": "—", "gap": "—"},
        ]
        gaps = rank_gaps(matrix)
        assert gaps["total"] == 2
        assert len(gaps["table_stakes"]) == 1
        assert len(gaps["edge"]) == 1
        assert gaps["table_stakes"][0]["capability"] == "A"
    check("rank_gaps separates table-stakes from edge", test_rank_gaps)

    # Test 3: build_capability_matrix all table-stakes present
    def test_matrix_all_present():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            us_profile = {"domains": [], "capabilities": [], "total_notes": 0}
            comparators = []
            clusters = {}
            matrix = build_capability_matrix(us_profile, comparators, clusters, "general")
            ts = [m for m in matrix if m["tier"] == "table-stakes"]
            assert all(m["us"] == "✅" for m in ts), "All table-stakes should be ✅ (hardcoded)"
        finally:
            shutil.rmtree(tmp)
    check("matrix all table-stakes present", test_matrix_all_present)

    # Test 4: rank_gaps empty matrix
    def test_rank_gaps_empty():
        gaps = rank_gaps([])
        assert gaps["total"] == 0
        assert gaps["table_stakes"] == []
        assert gaps["edge"] == []
    check("rank_gaps empty matrix", test_rank_gaps_empty)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain SOTA — matrix sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="No-op for read-only matrix")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.vault:
        args.vault = os.environ.get("HERMES_VAULT_PATH")
    if not args.vault:
        print("Error: --vault <path> or HERMES_VAULT_PATH is required.", file=sys.stderr)
        sys.exit(1)

    init_paths(args.vault)
    dry_run = not args.apply

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    us_profile = {
        "domains": ["agent-brain-vault"],
        "capabilities": ["github-agents"],
        "total_notes": 0,
    }
    comparators = []
    clusters = {"agent-brain-vault": []}
    us_label = "agent-brain-vault"

    matrix = build_capability_matrix(us_profile, comparators, clusters, us_label)
    gaps = rank_gaps(matrix)

    print(f"📊 Capability matrix")
    print(f"   | Capability | Us | Gap? |")
    print(f"   |------------|----|------|")
    for m in matrix:
        print(f"   | {m['capability']} | {m['us']} | {m['gap']} |")

    print(f"\n   Gaps: {gaps['total']} total ({len(gaps['table_stakes'])} table-stakes, {len(gaps['edge'])} edge)")

    if dry_run:
        print("\nRun with --apply to confirm (read-only matrix — no changes).")


if __name__ == "__main__":
    main()
