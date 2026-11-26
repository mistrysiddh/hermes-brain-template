#!/usr/bin/env python3
"""
Hermes Brain — Metrics Sub-Skill: sessions (metrics/sessions.py)

Collects session metrics from Daily/ archives:
  - total session count
  - sessions by month
  - date range (earliest → latest)

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply (no-op for read-only metric)
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python metrics/sessions.py --vault <path>
  python metrics/sessions.py --vault <path> --test
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


# ---------------------------------------------------------------------------
# collect_sessions — session metrics from Daily/ archives
# ---------------------------------------------------------------------------
def collect_sessions(vault_dir):
    """Compute session metrics from Daily/ archives."""
    daily_dirs = [
        os.path.join(vault_dir, "04-Archives", "Daily"),
        os.path.join(vault_dir, "Daily"),
    ]
    daily_dir = None
    for d in daily_dirs:
        if os.path.isdir(d):
            daily_dir = d
            break

    total = 0
    by_month = {}
    date_range = {"earliest": None, "latest": None}

    if daily_dir:
        for full, rel, name, content in walk_md(daily_dir):
            total += 1
            # Try to extract date from frontmatter created_at
            m = re.search(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})"', content)
            if m:
                date_str = f"{m.group(1)}-{m.group(2)}"
                by_month[date_str] = by_month.get(date_str, 0) + 1
                full_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                if date_range["earliest"] is None or full_date < date_range["earliest"]:
                    date_range["earliest"] = full_date
                if date_range["latest"] is None or full_date > date_range["latest"]:
                    date_range["latest"] = full_date
            else:
                # Fall back to filename date pattern
                dm = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", name)
                if dm:
                    date_str = f"{dm.group(1)}-{dm.group(2)}"
                    by_month[date_str] = by_month.get(date_str, 0) + 1
                    full_date = f"{dm.group(1)}-{dm.group(2)}-{dm.group(3)}"
                    if date_range["earliest"] is None or full_date < date_range["earliest"]:
                        date_range["earliest"] = full_date
                    if date_range["latest"] is None or full_date > date_range["latest"]:
                        date_range["latest"] = full_date

    return {
        "total_sessions": total,
        "by_month": dict(sorted(by_month.items())),
        "date_range": date_range,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 metrics/sessions.py Self-Test Suite")
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

    # Test 1: collect_sessions counts sessions with frontmatter dates
    def test_collect_sessions_frontmatter():
        tmp = tempfile.mkdtemp()
        try:
            daily_dir = os.path.join(tmp, "04-Archives", "Daily")
            os.makedirs(daily_dir)
            write_file(os.path.join(daily_dir, "2026-01-15.md"),
                       '---\ncreated_at: "2026-01-15"\n---\n# Session Jan 15')
            write_file(os.path.join(daily_dir, "2026-01-20.md"),
                       '---\ncreated_at: "2026-01-20"\n---\n# Session Jan 20')
            init_paths(tmp)
            sessions = collect_sessions(tmp)
            assert sessions["total_sessions"] == 2, f"Expected 2 sessions, got {sessions['total_sessions']}"
            assert sessions["by_month"].get("2026-01", 0) == 2
            assert sessions["date_range"]["earliest"] == "2026-01-15"
            assert sessions["date_range"]["latest"] == "2026-01-20"
        finally:
            shutil.rmtree(tmp)
    check("collect_sessions counts sessions with frontmatter dates", test_collect_sessions_frontmatter)

    # Test 2: collect_sessions filename date fallback
    def test_collect_sessions_filename_date():
        tmp = tempfile.mkdtemp()
        try:
            daily_dir = os.path.join(tmp, "Daily")
            os.makedirs(daily_dir)
            write_file(os.path.join(daily_dir, "2026-03-10.md"), "# Session Mar 10")
            write_file(os.path.join(daily_dir, "2026-03-25.md"), "# Session Mar 25")
            init_paths(tmp)
            sessions = collect_sessions(tmp)
            assert sessions["total_sessions"] == 2
            assert sessions["by_month"].get("2026-03", 0) == 2
        finally:
            shutil.rmtree(tmp)
    check("collect_sessions filename date fallback", test_collect_sessions_filename_date)

    # Test 3: collect_sessions empty vault (no Daily dir)
    def test_collect_sessions_empty():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            sessions = collect_sessions(tmp)
            assert sessions["total_sessions"] == 0
            assert sessions["by_month"] == {}
            assert sessions["date_range"]["earliest"] is None
            assert sessions["date_range"]["latest"] is None
        finally:
            shutil.rmtree(tmp)
    check("collect_sessions empty vault", test_collect_sessions_empty)

    # Test 4: collect_sessions mixed date sources
    def test_collect_sessions_mixed():
        tmp = tempfile.mkdtemp()
        try:
            daily_dir = os.path.join(tmp, "04-Archives", "Daily")
            os.makedirs(daily_dir)
            write_file(os.path.join(daily_dir, "frontmatter.md"),
                       '---\ncreated_at: "2026-02-10"\n---\n# Frontmatter dated')
            write_file(os.path.join(daily_dir, "2026-02-20.md"), "# Filename dated")
            init_paths(tmp)
            sessions = collect_sessions(tmp)
            assert sessions["total_sessions"] == 2
            assert sessions["by_month"].get("2026-02", 0) == 2
            assert sessions["date_range"]["earliest"] == "2026-02-10"
            assert sessions["date_range"]["latest"] == "2026-02-20"
        finally:
            shutil.rmtree(tmp)
    check("collect_sessions mixed date sources", test_collect_sessions_mixed)

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
        description="Hermes Brain Metrics — sessions sub-skill.",
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

    result = collect_sessions(VAULT)

    print(f"📅 Sessions metrics")
    print(f"   Total sessions: {result['total_sessions']}")
    dr = result["date_range"]
    if dr["earliest"] and dr["latest"]:
        print(f"   Date range: {dr['earliest']} → {dr['latest']}")
    if result["by_month"]:
        print(f"   Sessions by month:")
        for month, count in list(result["by_month"].items())[-12:]:
            print(f"     {month}: {count}")

    if dry_run:
        print("\nRun with --apply to confirm (read-only metric — no changes).")


if __name__ == "__main__":
    main()
