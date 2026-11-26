#!/usr/bin/env python3
"""
Hermes Brain — Metrics Sub-Skill: notes (metrics/notes.py)

Collects note-level metrics:
  - total note count
  - notes per top-level directory
  - recent activity (notes modified in N days)
  - directory sizes in bytes

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only metric)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python metrics/notes.py --vault <path>
  python metrics/notes.py --vault <path> --test
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


# ---------------------------------------------------------------------------
# collect_notes — note-level metrics
# ---------------------------------------------------------------------------
def collect_notes(vault_dir, days=30):
    """Compute note-level metrics."""
    total = 0
    by_dir = {}
    recent = 0
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    dir_sizes = {}

    for full, rel, name, content in walk_md(vault_dir):
        total += 1
        top_dir = rel.split("/")[0] if "/" in rel else "_root"
        by_dir[top_dir] = by_dir.get(top_dir, 0) + 1
        mtime = _get_mod_time(full)
        if mtime and mtime >= cutoff:
            recent += 1
        dir_sizes[top_dir] = dir_sizes.get(top_dir, 0) + len(content.encode("utf-8"))

    return {
        "total": total,
        "by_dir": dict(sorted(by_dir.items(), key=lambda x: -x[1])),
        "recent_days": recent,
        "dir_sizes_bytes": dir_sizes,
    }


def _get_mod_time(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 metrics/notes.py Self-Test Suite")
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

    # Test 1: collect_notes counts notes correctly
    def test_collect_notes_counts():
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "01-Projects"))
            os.makedirs(os.path.join(tmp, "03-Resources", "MOCs"))
            write_file(os.path.join(tmp, "01-Projects", "proj.md"), "# Project\n\nContent.")
            write_file(os.path.join(tmp, "03-Resources", "MOCs", "ai.md"), "# AI MOC\n\nSee [[Project]].")
            write_file(os.path.join(tmp, "README.md"), "# Root readme")
            init_paths(tmp)
            notes = collect_notes(tmp, days=30)
            assert notes["total"] == 2, f"Expected 2 notes (excl. README), got {notes['total']}"
            assert notes["by_dir"].get("01-Projects", 0) == 1
            assert notes["by_dir"].get("03-Resources", 0) == 1
        finally:
            shutil.rmtree(tmp)
    check("collect_notes counts notes correctly", test_collect_notes_counts)

    # Test 2: collect_notes recent_days filter
    def test_collect_notes_recent():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "recent.md"), "# Recent\n\nContent.")
            init_paths(tmp)
            notes = collect_notes(tmp, days=30)
            assert notes["recent_days"] == 1, f"Expected 1 recent, got {notes['recent_days']}"
        finally:
            shutil.rmtree(tmp)
    check("collect_notes recent_days filter", test_collect_notes_recent)

    # Test 3: collect_notes by_dir aggregation
    def test_collect_notes_by_dir():
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "A"))
            os.makedirs(os.path.join(tmp, "B"))
            write_file(os.path.join(tmp, "A", "a1.md"), "# A1")
            write_file(os.path.join(tmp, "A", "a2.md"), "# A2")
            write_file(os.path.join(tmp, "B", "b1.md"), "# B1")
            init_paths(tmp)
            notes = collect_notes(tmp, days=30)
            assert notes["by_dir"]["A"] == 2, f"Expected A=2, got {notes['by_dir'].get('A')}"
            assert notes["by_dir"]["B"] == 1, f"Expected B=1, got {notes['by_dir'].get('B')}"
        finally:
            shutil.rmtree(tmp)
    check("collect_notes by_dir aggregation", test_collect_notes_by_dir)

    # Test 4: collect_notes dir_sizes_bytes
    def test_collect_notes_dir_sizes():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "s.md"), "# S\n\nSome content here for size.")
            init_paths(tmp)
            notes = collect_notes(tmp, days=30)
            assert "_root" in notes["dir_sizes_bytes"], "Expected _root in dir_sizes_bytes"
            assert notes["dir_sizes_bytes"]["_root"] > 0
        finally:
            shutil.rmtree(tmp)
    check("collect_notes dir_sizes_bytes", test_collect_notes_dir_sizes)

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
        description="Hermes Brain Metrics — notes sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--days", type=int, default=30, help="Activity window in days (default: 30)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="No-op for read-only metric")
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

    result = collect_notes(VAULT, days=args.days)

    print(f"📊 Notes metrics (last {args.days} days)")
    print(f"   Total notes: {result['total']}")
    print(f"   Recent ({args.days} days): {result['recent_days']}")
    print(f"   Top directories:")
    for d, c in list(result["by_dir"].items())[:10]:
        size_kb = round(result["dir_sizes_bytes"].get(d, 0) / 1024, 1)
        print(f"     {d}: {c} notes, {size_kb} KB")

    if dry_run:
        print("\nRun with --apply to confirm (read-only metric — no changes).")


if __name__ == "__main__":
    main()
