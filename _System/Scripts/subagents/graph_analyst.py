#!/usr/bin/env python3
"""
Hermes Brain — Graph Analyst Sub-Skill (subagents/graph_analyst.py)

Performs monthly navigation analysis — MOC health, clusters, centrality,
dead ends. Part of the subagents multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  python subagents/graph_analyst.py --vault <path> scan

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
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


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def walk_md(vault_dir, exclude_dirs=None, exclude_files=None):
    """Walk vault_dir yielding (full_path, rel_path, name, content) for .md files."""
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash"}
    exclude_files = exclude_files or {"README.md", "manifest.jsonl"}
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            if f in exclude_files:
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault_dir).replace("\\", "/")
            content = read_file(full)
            yield full, rel, os.path.splitext(f)[0], content


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


# ---------------------------------------------------------------------------
# Graph Analyst — monthly navigation analysis
# ---------------------------------------------------------------------------
def run_graph_analyst(vault_dir):
    """Analyze vault navigation graph — MOC health, centrality, dead ends."""
    notes = []
    link_graph = {}  # rel_path -> set of linked targets

    for full, rel, name, content in walk_md(vault_dir):
        notes.append({"rel_path": rel, "name": name, "content": content})
        links = set()
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip().split("|")[0].strip()
            links.add(target)
        link_graph[rel] = links

    # Count incoming links (centrality)
    incoming = {}
    for rel, targets in link_graph.items():
        for t in targets:
            incoming[t] = incoming.get(t, 0) + 1

    # Most linked notes (central nodes)
    central = sorted(incoming.items(), key=lambda x: -x[1])[:10]

    # Notes with no outgoing links (dead ends)
    dead_ends = [rel for rel, targets in link_graph.items() if not targets]

    # MOC detection — notes with many outgoing links
    mocs = sorted(
        [(rel, len(targets)) for rel, targets in link_graph.items()],
        key=lambda x: -x[1],
    )[:10]

    # Clusters by directory
    dir_links = {}
    for rel, targets in link_graph.items():
        d = rel.split("/")[0] if "/" in rel else "_root"
        dir_links.setdefault(d, set())
        for t in targets:
            td = t.split("/")[0] if "/" in t else "_root"
            if td != d:
                dir_links[d].add(td)

    return {
        "total_notes": len(notes),
        "total_links": sum(len(t) for t in link_graph.values()),
        "central_nodes": central,
        "dead_ends": dead_ends[:20],
        "dead_end_count": len(dead_ends),
        "top_mocs": mocs,
        "directory_links": {k: sorted(v) for k, v in dir_links.items()},
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 subagents/graph_analyst.py Self-Test Suite")
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

    # Test 1: graph_analyst analyzes vault
    def test_graph_analyst():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# A\n\nSee [[B]].")
            write_file(os.path.join(tmp, "b.md"), "# B\n\nSee [[A]] and [[C]].")
            write_file(os.path.join(tmp, "c.md"), "# C\n\nStandalone note.")
            graph = run_graph_analyst(tmp)
            assert graph["total_notes"] == 3
            assert graph["total_links"] >= 3
        finally:
            shutil.rmtree(tmp)
    check("graph analyst analyzes vault", test_graph_analyst)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Graph Analyst — monthly navigation analysis.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("scan", help="Run monthly navigation analysis (dry-run report)")
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

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    if args.command and args.command != "scan":
        print(f"Error: Unknown command '{args.command}'. Use 'scan'.", file=sys.stderr)
        sys.exit(1)

    graph = run_graph_analyst(VAULT)

    print(f"📊 Graph Analyst — monthly navigation analysis")
    print(f"   Total notes: {graph['total_notes']}")
    print(f"   Total links: {graph['total_links']}")
    print(f"   Dead ends: {graph['dead_end_count']}")
    print()

    if graph["central_nodes"]:
        print("### Most linked nodes (centrality)")
        print("| Note | Incoming links |")
        print("|------|----------------|")
        for rel, count in graph["central_nodes"][:10]:
            print(f"| `{rel}` | {count} |")
        print()

    if graph["dead_ends"]:
        print("### Dead ends (no outgoing links)")
        for d in graph["dead_ends"][:10]:
            print(f"  - `{d}`")
        print()

    if graph["top_mocs"]:
        print("### Top MOCs (most outgoing links)")
        print("| Note | Outgoing links |")
        print("|------|----------------|")
        for rel, count in graph["top_mocs"][:10]:
            print(f"| `{rel}` | {count} |")
        print()


if __name__ == "__main__":
    main()
