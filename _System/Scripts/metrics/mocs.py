#!/usr/bin/env python3
"""
Hermes Brain — Metrics Sub-Skill: mocs (metrics/mocs.py)

Collects MOC (Map of Content) health metrics:
  - total MOC count
  - healthy MOCs (contain wikilinks)
  - orphaned MOCs (no links)

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only metric)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python metrics/mocs.py --vault <path>
  python metrics/mocs.py --vault <path> --test
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
# collect_mocs — MOC health metrics
# ---------------------------------------------------------------------------
def collect_mocs(vault_dir):
    """Compute MOC health metrics."""
    moc_dirs = [
        os.path.join(vault_dir, "03-Resources", "MOCs"),
        os.path.join(vault_dir, "MOCs"),
    ]
    moc_dir = None
    for d in moc_dirs:
        if os.path.isdir(d):
            moc_dir = d
            break

    total_mocs = 0
    orphaned = []
    healthy = 0

    if moc_dir:
        all_note_rels = {rel for _, rel, _, _ in walk_md(vault_dir)}
        for full, rel, name, content in walk_md(moc_dir):
            total_mocs += 1
            links = list(WIKILINK_RE.finditer(content))
            if links:
                healthy += 1
            else:
                orphaned.append(rel)

    return {
        "total_mocs": total_mocs,
        "healthy_mocs": healthy,
        "orphaned_mocs": orphaned[:10],
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 metrics/mocs.py Self-Test Suite")
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

    # Test 1: collect_mocs counts healthy and orphaned MOCs
    def test_collect_mocs():
        tmp = tempfile.mkdtemp()
        try:
            moc_dir = os.path.join(tmp, "03-Resources", "MOCs")
            os.makedirs(moc_dir)
            write_file(os.path.join(moc_dir, "ai.md"), "# AI MOC\n\nSee [[Project]] and [[ML]].")
            write_file(os.path.join(moc_dir, "orphan.md"), "# Orphan MOC\n\nNo links here.")
            init_paths(tmp)
            mocs = collect_mocs(tmp)
            assert mocs["total_mocs"] == 2, f"Expected 2 MOCs, got {mocs['total_mocs']}"
            assert mocs["healthy_mocs"] == 1, f"Expected 1 healthy MOC, got {mocs['healthy_mocs']}"
            assert len(mocs["orphaned_mocs"]) == 1
            assert "orphan.md" in mocs["orphaned_mocs"][0]
        finally:
            shutil.rmtree(tmp)
    check("collect_mocs counts healthy and orphaned MOCs", test_collect_mocs)

    # Test 2: collect_mocs all healthy
    def test_collect_mocs_all_healthy():
        tmp = tempfile.mkdtemp()
        try:
            moc_dir = os.path.join(tmp, "MOCs")
            os.makedirs(moc_dir)
            write_file(os.path.join(moc_dir, "a.md"), "# A\n\n[[B]]")
            write_file(os.path.join(moc_dir, "b.md"), "# B\n\n[[A]]")
            init_paths(tmp)
            mocs = collect_mocs(tmp)
            assert mocs["total_mocs"] == 2
            assert mocs["healthy_mocs"] == 2
            assert mocs["orphaned_mocs"] == []
        finally:
            shutil.rmtree(tmp)
    check("collect_mocs all healthy", test_collect_mocs_all_healthy)

    # Test 3: collect_mocs no MOCs dir
    def test_collect_mocs_no_dir():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            mocs = collect_mocs(tmp)
            assert mocs["total_mocs"] == 0
            assert mocs["healthy_mocs"] == 0
            assert mocs["orphaned_mocs"] == []
        finally:
            shutil.rmtree(tmp)
    check("collect_mocs no MOCs dir", test_collect_mocs_no_dir)

    # Test 4: collect_mocs orphaned MOC examples limit
    def test_collect_mocs_orphaned_limit():
        tmp = tempfile.mkdtemp()
        try:
            moc_dir = os.path.join(tmp, "03-Resources", "MOCs")
            os.makedirs(moc_dir)
            for i in range(15):
                write_file(os.path.join(moc_dir, f"orphan{i}.md"), f"# Orphan {i}\n\nNo links.")
            init_paths(tmp)
            mocs = collect_mocs(tmp)
            assert mocs["total_mocs"] == 15
            assert mocs["healthy_mocs"] == 0
            assert len(mocs["orphaned_mocs"]) == 10  # limited to 10 examples
        finally:
            shutil.rmtree(tmp)
    check("collect_mocs orphaned MOC examples limit", test_collect_mocs_orphaned_limit)

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
        description="Hermes Brain Metrics — mocs sub-skill.",
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

    result = collect_mocs(VAULT)

    print(f"🗺️  MOCs metrics")
    print(f"   Total MOCs: {result['total_mocs']}")
    print(f"   Healthy MOCs (contain wikilinks): {result['healthy_mocs']}")
    print(f"   Orphaned MOCs (no links): {result['total_mocs'] - result['healthy_mocs']}")
    if result["orphaned_mocs"]:
        print(f"   Orphaned examples:")
        for moc in result["orphaned_mocs"]:
            print(f"     {moc}")

    if dry_run:
        print("\nRun with --apply to confirm (read-only metric — no changes).")


if __name__ == "__main__":
    main()
