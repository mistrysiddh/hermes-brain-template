#!/usr/bin/env python3
"""
Hermes Brain — Metrics Sub-Skill: tags (metrics/tags.py)

Collects tag frequency distribution from vault notes.

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only metric)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python metrics/tags.py --vault <path>
  python metrics/tags.py --vault <path> --test
"""

import argparse
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


TAG_RE = re.compile(r"(?:^|\s)#([\w\-/]+)", re.M)


# ---------------------------------------------------------------------------
# collect_tags — tag frequency distribution
# ---------------------------------------------------------------------------
def collect_tags(vault_dir, top_n=20):
    """Compute tag frequency distribution."""
    tag_counts = {}
    for _, _, _, content in walk_md(vault_dir):
        for tag in TAG_RE.findall(content):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
    return {"total_unique_tags": len(tag_counts), "top_tags": sorted_tags[:top_n]}


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 metrics/tags.py Self-Test Suite")
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

    # Test 1: collect_tags extracts tags correctly
    def test_collect_tags():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "t.md"), "# Tags\n\n#ai #ml #ai #research")
            init_paths(tmp)
            tags = collect_tags(tmp)
            assert tags["top_tags"][0][0] == "ai", f"Expected 'ai' as top tag, got {tags['top_tags'][0]}"
            assert tags["top_tags"][0][1] == 2, f"Expected count 2 for 'ai', got {tags['top_tags'][0][1]}"
            assert tags["total_unique_tags"] == 3
        finally:
            shutil.rmtree(tmp)
    check("collect_tags extracts tags correctly", test_collect_tags)

    # Test 2: collect_tags nested tags (#ai/ml)
    def test_collect_tags_nested():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "n.md"), "# Nested\n\n#ai/ml #ai/nlp #ml/dl")
            init_paths(tmp)
            tags = collect_tags(tmp)
            assert tags["total_unique_tags"] == 3
            assert ("ai/ml", 1) in tags["top_tags"]
            assert ("ai/nlp", 1) in tags["top_tags"]
            assert ("ml/dl", 1) in tags["top_tags"]
        finally:
            shutil.rmtree(tmp)
    check("collect_tags nested tags", test_collect_tags_nested)

    # Test 3: collect_tags empty vault
    def test_collect_tags_empty():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "e.md"), "# Empty\n\nNo tags here.")
            init_paths(tmp)
            tags = collect_tags(tmp)
            assert tags["total_unique_tags"] == 0
            assert tags["top_tags"] == []
        finally:
            shutil.rmtree(tmp)
    check("collect_tags empty vault", test_collect_tags_empty)

    # Test 4: collect_tags top_n limit
    def test_collect_tags_top_n():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "many.md"), "# Many\n\n#t1 #t2 #t3 #t4 #t5")
            init_paths(tmp)
            tags = collect_tags(tmp, top_n=3)
            assert len(tags["top_tags"]) == 3, f"Expected 3 top tags, got {len(tags['top_tags'])}"
        finally:
            shutil.rmtree(tmp)
    check("collect_tags top_n limit", test_collect_tags_top_n)

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
        description="Hermes Brain Metrics — tags sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--top-n", type=int, default=20, help="Max top tags to show (default: 20)")
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

    result = collect_tags(VAULT, top_n=args.top_n)

    print(f"🏷️  Tags metrics")
    print(f"   Unique tags: {result['total_unique_tags']}")
    if result["top_tags"]:
        print(f"   Top tags:")
        for tag, count in result["top_tags"][:15]:
            print(f"     #{tag}: {count}")

    if dry_run:
        print("\nRun with --apply to confirm (read-only metric — no changes).")


if __name__ == "__main__":
    main()
