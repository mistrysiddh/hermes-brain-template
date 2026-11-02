#!/usr/bin/env python3
"""
Hermes Brain — Metrics Sub-Skill: links (metrics/links.py)

Collects wikilink metrics:
  - total wikilink count
  - unique targets
  - broken link detection
  - link density (links per note)

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only metric)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python metrics/links.py --vault <path>
  python metrics/links.py --vault <path> --test
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


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


# ---------------------------------------------------------------------------
# collect_links — wikilink metrics
# ---------------------------------------------------------------------------
def collect_links(vault_dir):
    """Compute wikilink metrics: total links, unique targets, broken links."""
    total_links = 0
    unique_targets = set()
    broken = []
    all_notes = {rel: full for full, rel, _, _ in walk_md(vault_dir)}

    for full, rel, name, content in walk_md(vault_dir):
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip()
            # Strip alias if present: [[target|alias]]
            if "|" in target:
                target = target.split("|")[0].strip()
            total_links += 1
            unique_targets.add(target)
            # Check if target exists as a note
            target_md = target + ".md"
            target_rel = target_md
            found = target_rel in all_notes
            if not found:
                for existing_rel in all_notes:
                    if existing_rel.lower().endswith(target_md.lower()):
                        found = True
                        break
            if not found:
                broken.append({"source": rel, "target": target})

    return {
        "total_links": total_links,
        "unique_targets": len(unique_targets),
        "broken_links": len(broken),
        "broken_examples": broken[:5],
        "link_density": round(total_links / max(1, len(all_notes)), 2),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 metrics/links.py Self-Test Suite")
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

    # Test 1: collect_links finds links and detects broken ones
    def test_collect_links():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "a.md"), "# A\n\nSee [[B]] and [[C|alias]].")
            write_file(os.path.join(tmp, "b.md"), "# B\n\nBack to [[A]].")
            init_paths(tmp)
            links = collect_links(tmp)
            assert links["total_links"] >= 3, f"Expected >=3 links, got {links['total_links']}"
            assert links["broken_links"] == 1, f"Expected 1 broken link (C), got {links['broken_links']}"
            assert links["link_density"] > 0
        finally:
            shutil.rmtree(tmp)
    check("collect_links finds links and detects broken ones", test_collect_links)

    # Test 2: collect_links alias handling
    def test_collect_links_alias():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "x.md"), "# X\n\nSee [[Y|Custom Label]] and [[Z]].")
            write_file(os.path.join(tmp, "y.md"), "# Y")
            init_paths(tmp)
            links = collect_links(tmp)
            assert links["broken_links"] == 1, f"Expected 1 broken link (Z), got {links['broken_links']}"
            assert links["total_links"] == 2, f"Expected 2 links, got {links['total_links']}"
        finally:
            shutil.rmtree(tmp)
    check("collect_links alias handling", test_collect_links_alias)

    # Test 3: collect_links unique targets
    def test_collect_links_unique():
        tmp = tempfile.mkdtemp()
        try:
            write_file(os.path.join(tmp, "p.md"), "# P\n\nSee [[Q]] and [[Q]] again.")
            write_file(os.path.join(tmp, "q.md"), "# Q")
            init_paths(tmp)
            links = collect_links(tmp)
            assert links["total_links"] == 2, f"Expected 2 total links, got {links['total_links']}"
            assert links["unique_targets"] == 1, f"Expected 1 unique target, got {links['unique_targets']}"
            assert links["broken_links"] == 0
        finally:
            shutil.rmtree(tmp)
    check("collect_links unique targets", test_collect_links_unique)

    # Test 4: collect_links empty vault
    def test_collect_links_empty():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            links = collect_links(tmp)
            assert links["total_links"] == 0
            assert links["unique_targets"] == 0
            assert links["broken_links"] == 0
            assert links["link_density"] == 0
        finally:
            shutil.rmtree(tmp)
    check("collect_links empty vault", test_collect_links_empty)

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
        description="Hermes Brain Metrics — links sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
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

    result = collect_links(VAULT)

    print(f"🔗 Links metrics")
    print(f"   Total wikilinks: {result['total_links']}")
    print(f"   Unique targets: {result['unique_targets']}")
    print(f"   Broken links: {result['broken_links']}")
    print(f"   Link density (per note): {result['link_density']}")
    if result["broken_examples"]:
        print(f"   Broken examples:")
        for ex in result["broken_examples"]:
            print(f"     [[{ex['target']}]] in {ex['source']}")

    if dry_run:
        print("\nRun with --apply to confirm (read-only metric — no changes).")


if __name__ == "__main__":
    main()
