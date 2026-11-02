#!/usr/bin/env python3
"""
Hermes Brain — Reviewer Sub-Skill (subagents/reviewer.py)

Read-only vault audit — checks for broken wikilinks, orphaned notes, and drift.
Part of the subagents multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  python subagents/reviewer.py --vault <path> scan

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
# Reviewer — read-only vault audit
# ---------------------------------------------------------------------------
def run_reviewer(vault_dir):
    """Read-only audit of the vault."""
    total_notes = 0
    total_links = 0
    broken_links = []
    orphaned = []
    by_dir = {}
    all_rel_paths = set()

    # First pass: collect all notes
    notes = []
    for full, rel, name, content in walk_md(vault_dir):
        total_notes += 1
        all_rel_paths.add(rel)
        top_dir = rel.split("/")[0] if "/" in rel else "_root"
        by_dir[top_dir] = by_dir.get(top_dir, 0) + 1
        notes.append((full, rel, name, content))

    # Second pass: check links and find orphans
    linked_targets = set()
    for full, rel, name, content in notes:
        for m in WIKILINK_RE.finditer(content):
            total_links += 1
            target = m.group(1).strip().split("|")[0].strip()
            target_md = target + ".md"
            if target_md not in all_rel_paths and target not in all_rel_paths:
                broken_links.append({
                    "source": rel,
                    "target": target,
                })
            linked_targets.add(target)

    # Find orphaned notes (no incoming links from any other note)
    for full, rel, name, content in notes:
        if name not in linked_targets and rel.split("/")[-1].replace(".md", "") not in linked_targets:
            orphaned.append(rel)

    return {
        "total_notes": total_notes,
        "total_links": total_links,
        "broken_links": broken_links[:20],
        "broken_count": len(broken_links),
        "orphaned": orphaned[:20],
        "orphaned_count": len(orphaned),
        "by_dir": dict(sorted(by_dir.items(), key=lambda x: -x[1])),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 subagents/reviewer.py Self-Test Suite")
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

    # Test 1: run_reviewer finds notes and links
    def test_reviewer():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "A.md"), "# A\n\nSee [[B]].")
            write_file(os.path.join(tmp, "B.md"), "# B\n\nBack to [[A]].")
            result = run_reviewer(tmp)
            assert result["total_notes"] == 2
            assert result["total_links"] >= 1
            assert result["broken_count"] == 0
        finally:
            shutil.rmtree(tmp)
    check("reviewer finds notes and links", test_reviewer)

    # Test 2: run_reviewer detects broken links
    def test_reviewer_broken():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# A\n\nSee [[Nonexistent]].")
            result = run_reviewer(tmp)
            assert result["broken_count"] == 1
            assert result["broken_links"][0]["target"] == "Nonexistent"
        finally:
            shutil.rmtree(tmp)
    check("reviewer detects broken links", test_reviewer_broken)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Reviewer — read-only vault audit.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("scan", help="Run read-only vault audit (dry-run report)")
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

    result = run_reviewer(VAULT)

    print(f"📋 Reviewer — vault audit report")
    print(f"   Total notes: {result['total_notes']}")
    print(f"   Total wikilinks: {result['total_links']}")
    print(f"   Broken links: {result['broken_count']}")
    print(f"   Orphaned notes: {result['orphaned_count']}")
    print()

    if result["broken_links"]:
        print("### Broken links (first 20):")
        for b in result["broken_links"]:
            print(f"  - [[{b['target']}]] in `{b['source']}`")
        print()

    if result["orphaned"]:
        print("### Orphaned notes (first 20):")
        for o in result["orphaned"]:
            print(f"  - `{o}`")
        print()

    print("### Notes by top directory:")
    print("| Directory | Count |")
    print("|-----------|-------|")
    for d, count in list(result["by_dir"].items())[:10]:
        print(f"| {d} | {count} |")


if __name__ == "__main__":
    main()
