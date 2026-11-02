#!/usr/bin/env python3
"""
Hermes Brain — Converse Learn Lesson Sub-Skill (converse_learn/lesson.py)

Extracts lessons (mistakes, anti-patterns, what went wrong) from archived
session notes. Part of the converse_learn multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Usage:
  python converse_learn/lesson.py --vault <path> scan --days 14
  python converse_learn/lesson.py --vault <path> scan --days 14 --apply

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
# Lesson category — mistakes, anti-patterns, what went wrong
# ---------------------------------------------------------------------------
LESSON_PATTERNS = [
    r"(?:mistake|error|fail|bug|issue|problem)\s*:?\s*(.+)",
    r"(?:learned|learn)\s+that\s+(.+)",
    r"(?:avoid|don't|do not)\s+(.+)",
    r"(?:should\s+not|shouldn't)\s+(.+)",
    r"(?:wrong|incorrect|broken)\s*:?\s*(.+)",
]


def extract_lesson_items(content):
    """Extract lesson items from session content."""
    items = []
    for pattern in LESSON_PATTERNS:
        for m in re.finditer(pattern, content, re.I):
            text = m.group(1).strip() if m.group(1) else m.group(0).strip()
            if len(text) > 3:
                items.append({
                    "text": text[:200],
                    "category": "lesson",
                })
    return items


def run_lesson_scan(vault_dir, days=14, dry_run=True):
    """Scan vault sessions for lesson items."""
    import datetime as dt
    cutoff = None
    if days:
        cutoff = datetime.datetime.now(dt.timezone.utc) - datetime.timedelta(days=days)

    results = []
    for full, rel, name, content in walk_md(vault_dir):
        if cutoff:
            try:
                ts = os.path.getmtime(full)
                mtime = datetime.datetime.fromtimestamp(ts, dt.timezone.utc)
                if mtime < cutoff:
                    continue
            except Exception:
                pass

        items = extract_lesson_items(content)
        for item in items:
            results.append({
                "source": rel,
                "name": name,
                "category": item["category"],
                "text": item["text"],
                "applied": False,
                "reason": "dry-run preview" if dry_run else "ready for confirmation",
            })

            if not dry_run:
                results[-1]["applied"] = True
                results[-1]["reason"] = "confirmed for lesson"

    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 converse_learn/lesson.py Self-Test Suite")
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

    # Test 1: extract_lesson_items
    def test_extract():
        content = "Mistake: forgot to save file. Learned that autosave is important. Avoid using tabs."
        items = extract_lesson_items(content)
        assert len(items) >= 1
        assert items[0]["category"] == "lesson"
    check("extract_lesson_items works", test_extract)

    # Test 2: run_lesson_scan finds items
    def test_scan():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "session.md"), "# Session\n\nMistake: forgot to save file. Avoid using tabs.")
            results = run_lesson_scan(tmp, days=30, dry_run=True)
            assert len(results) >= 1
            assert results[0]["applied"] is False
        finally:
            shutil.rmtree(tmp)
    check("run_lesson_scan finds items", test_scan)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Converse Learn Lesson — extract lessons from sessions.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    p_scan = sub.add_parser("scan", help="Scan sessions for lesson items (dry-run report)")
    p_scan.add_argument("--days", type=int, default=14, help="Days of sessions to scan (default: 14)")
    parser.add_argument("--apply", action="store_true", help="Apply findings (overrides --dry-run)")
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

    results = run_lesson_scan(VAULT, days=args.days, dry_run=dry_run)

    print(f"📚 Lesson scan — scanning vault for lesson items")
    print(f"   Found {len(results)} item(s)")
    print()

    if not results:
        print("✅ No lesson items found.")
        return

    print("| Source | Category | Text |")
    print("|--------|----------|------|")
    for r in results[:30]:
        text = r["text"][:60]
        print(f"| `{r['source']}` | {r['category']} | {text} |")

    if len(results) > 30:
        print(f"| ... and {len(results) - 30} more | | |")

    print()
    if dry_run:
        print("Run with --apply to confirm lesson items.")
    else:
        print(f"✅ Confirmed {len(results)} lesson item(s).")


if __name__ == "__main__":
    main()
