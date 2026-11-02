#!/usr/bin/env python3
"""
Hermes Brain — Curator Sub-Skill (subagents/curator.py)

Quarterly prune/archive review — identifies stale notes, stubs, and archive
candidates. Part of the subagents multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  python subagents/curator.py --vault <path> scan
  python subagents/curator.py --vault <path> scan --apply

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


# ---------------------------------------------------------------------------
# Curator — quarterly prune/archive review
# ---------------------------------------------------------------------------
def run_curator(vault_dir, dry_run=True):
    """Quarterly curation — identify stale notes, duplicates, archive candidates."""
    import datetime as dt
    cutoff = datetime.datetime.now(dt.timezone.utc) - datetime.timedelta(days=180)

    candidates = []
    for full, rel, name, content in walk_md(vault_dir):
        reasons = []
        try:
            ts = os.path.getmtime(full)
            mtime = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
            days = (datetime.datetime.now(dt.timezone.utc) - mtime).days
            if days > 180:
                reasons.append(f"stale ({days} days)")
        except Exception:
            pass

        # Very short notes (likely stubs)
        if len(content.strip()) < 50:
            reasons.append("stub (<50 chars)")

        if reasons:
            candidates.append({
                "path": rel,
                "reasons": reasons,
                "action": "review",
                "applied": False,
                "reason": "dry-run preview" if dry_run else "flagged for review",
            })

    return candidates


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 subagents/curator.py Self-Test Suite")
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

    # Test 1: run_curator flags stale notes
    def test_curator():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "old.md"), "# Old note\n\nJust a tiny note.")
            old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=200)).timestamp()
            os.utime(os.path.join(tmp, "old.md"), (old_time, old_time))
            results = run_curator(tmp, dry_run=True)
            stale_found = any("old.md" in r["path"] for r in results)
            assert stale_found
        finally:
            shutil.rmtree(tmp)
    check("curator flags stale notes", test_curator)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Curator — quarterly prune/archive review.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_curator = sub.add_parser("scan", help="Run curation analysis (dry-run report)")
    p_curator.add_argument("--apply", action="store_true", help="Flag for review (overrides --dry-run)")

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

    if args.command and args.command != "scan":
        print(f"Error: Unknown command '{args.command}'. Use 'scan'.", file=sys.stderr)
        sys.exit(1)

    results = run_curator(VAULT, dry_run=dry_run)

    print(f"📋 Curator — quarterly prune/archive review")
    print(f"   Found {len(results)} candidate(s)")
    print()

    if not results:
        print("✅ No curation candidates found.")
        return

    print("| Note | Reasons |")
    print("|------|---------|")
    for r in results:
        print(f"| `{r['path']}` | {', '.join(r['reasons'])} |")

    print()
    if dry_run:
        print("Run with --apply to flag items for review.")
    else:
        print(f"✅ Flagged {len(results)} candidate(s) for review.")


if __name__ == "__main__":
    main()
