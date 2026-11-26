#!/usr/bin/env python3
"""
Hermes Brain — Ingestor Sub-Skill (subagents/ingestor.py)

Ingests new material from `raw/` into the vault as properly structured notes.
Part of the subagents multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Usage:
  python subagents/ingestor.py --vault <path> scan
  python subagents/ingestor.py --vault <path> scan --apply

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
RAW_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, RAW_DIR
    VAULT = os.path.abspath(vault_path)
    RAW_DIR = os.path.join(VAULT, "raw")


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


def slugify(text):
    slug = "".join(c if c.isalnum() or c in "-" else "-" for c in text.strip().lower()).strip("-_")
    return slug or "untitled"


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
# Ingestor — scan raw/ and ingest into vault
# ---------------------------------------------------------------------------
def scan_raw(vault_dir):
    """Scan raw/ directory for new material to ingest."""
    raw_dir = os.path.join(vault_dir, "raw")
    items = []
    if not os.path.isdir(raw_dir):
        return items
    for full, rel, name, content in walk_md(raw_dir):
        items.append({
            "path": full,
            "rel_path": rel,
            "name": name,
            "content": content,
        })
    return items


def determine_target(content, name):
    """Determine target directory based on content analysis."""
    lower = content.lower()
    if re.search(r"(project|build|deploy|setup|install|sprint|milestone|roadmap)", lower):
        return "01-Projects"
    elif re.search(r"(area|topic|domain|field|subject|discipline)", lower):
        return "02-Areas"
    elif re.search(r"(resource|reference|link|tool|template|guide|how-to)", lower):
        return "03-Resources"
    else:
        return "04-Archives"


def run_ingestor(vault_dir, dry_run=True):
    """Run the ingestor agent."""
    items = scan_raw(vault_dir)
    results = []
    for item in items:
        target_dir = determine_target(item["content"], item["name"])
        target_name = slugify(item["name"])
        target_rel = os.path.join(target_dir, f"{target_name}.md")
        target_full = os.path.join(vault_dir, target_rel)

        results.append({
            "source": item["rel_path"],
            "target": target_rel,
            "action": "ingest",
            "applied": False,
            "reason": "dry-run preview" if dry_run else "ingested",
        })

        if not dry_run:
            write_file(target_full, item["content"])
            results[-1]["applied"] = True
            results[-1]["reason"] = "ingested"

    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 subagents/ingestor.py Self-Test Suite")
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

    # Test 1: ingestor_scan finds new material
    def test_scan():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "raw"), exist_ok=True)
            write_file(os.path.join(tmp, "raw", "idea.md"), "# New Idea\n\nA project idea about AI agents.")
            items = scan_raw(tmp)
            assert len(items) == 1
            assert items[0]["name"] == "idea"
        finally:
            shutil.rmtree(tmp)
    check("ingestor_scan finds new material", test_scan)

    # Test 2: determine_target routes correctly
    def test_determine_target():
        assert determine_target("# Project Alpha\n\nBuild the AI system.", "proj") == "01-Projects"
        assert determine_target("# Topic Area\n\nAbout machine learning.", "topic") == "02-Areas"
        assert determine_target("# Resource\n\nLink to docs.", "res") == "03-Resources"
        assert determine_target("# Random note\n\nJust thoughts.", "misc") == "04-Archives"
    check("determine_target routes correctly", test_determine_target)

    # Test 3: run_ingestor dry-run
    def test_ingestor_dryrun():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "raw"), exist_ok=True)
            write_file(os.path.join(tmp, "raw", "test.md"), "# Test Note\n\nContent.")
            results = run_ingestor(tmp, dry_run=True)
            assert len(results) == 1
            assert results[0]["applied"] is False
            assert results[0]["reason"] == "dry-run preview"
            # Verify nothing was written
            assert not os.path.exists(os.path.join(tmp, results[0]["target"]))
        finally:
            shutil.rmtree(tmp)
    check("run_ingestor dry-run does not write", test_ingestor_dryrun)

    # Test 4: run_ingestor apply writes files
    def test_ingestor_apply():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "raw"), exist_ok=True)
            write_file(os.path.join(tmp, "raw", "proj.md"), "# Project Alpha\n\nBuild AI.")
            results = run_ingestor(tmp, dry_run=False)
            assert len(results) == 1
            assert results[0]["applied"] is True
            assert results[0]["reason"] == "ingested"
            target_path = os.path.join(tmp, results[0]["target"])
            assert os.path.exists(target_path)
            content = read_file(target_path)
            assert "Project Alpha" in content
        finally:
            shutil.rmtree(tmp)
    check("run_ingestor apply writes files", test_ingestor_apply)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Ingestor — scan raw/ and ingest new material into vault.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("scan", help="Scan raw/ and ingest new material into vault (dry-run report)")
    parser.add_argument("--apply", action="store_true", help="Apply ingestion (overrides --dry-run)")
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

    if args.command and args.command != "scan":
        print(f"Error: Unknown command '{args.command}'. Use 'scan'.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    results = run_ingestor(VAULT, dry_run=dry_run)

    print(f"📥 Ingestor — scanned raw/ for new material")
    print(f"   Found {len(results)} item(s) to ingest")
    print()

    if not results:
        print("✅ No new material to ingest.")
        return

    print("| Source | Target | Action |")
    print("|--------|--------|--------|")
    for r in results:
        print(f"| `{r['source']}` | `{r['target']}` | {r['action']} |")

    print()
    if dry_run:
        print("Run with --apply to ingest the items above.")
    else:
        print(f"✅ Ingested {len(results)} item(s) into the vault.")


if __name__ == "__main__":
    main()
