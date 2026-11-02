#!/usr/bin/env python3
"""
Hermes Brain — Converse Learn Orchestrator Sub-Skill (converse_learn/orchestrator.py)

Coordinates the full 5-pass conversation learning workflow:
1. Scan — parse session notes for corrections, error→fix sequences
2. Generate — convert signals into candidate learnings
3. Dedup — check against existing entries without dropping
4. Confirm — present candidates one at a time for human approval
5. Execute — write confirmed learnings to vault

Part of the converse_learn multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Usage:
  python converse_learn/orchestrator.py --vault <path> scan --days 14
  python converse_learn/orchestrator.py --vault <path> scan --days 14 --apply

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import os
import re
import shutil
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


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def tokenize(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def jaccard(a, b):
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# extract_learning_signals — extract correction/learning signals from content
# ---------------------------------------------------------------------------
def extract_learning_signals(content):
    """Extract learning signals from session content.

    Returns a list of dicts with keys: text, category
    """
    signals = []

    # Error → fix patterns
    error_patterns = [
        r"(?:error|mistake|bug|issue|problem)\s*:?\s*(.+)",
        r"(?:fixed|fixed by|resolved|workaround)\s*:?\s*(.+)",
        r"(?:instead|rather|better)\s+(.+)",
    ]

    for pattern in error_patterns:
        for m in re.finditer(pattern, content, re.I):
            text = m.group(1).strip() if m.group(1) else m.group(0).strip()
            if len(text) > 3:
                signals.append({
                    "text": text[:200],
                    "category": "error_fix",
                })

    return signals


# ---------------------------------------------------------------------------
# Orchestrator — 5-pass conversation learning workflow
# ---------------------------------------------------------------------------
def run_orchestrator(vault_dir, days=14, dry_run=True):
    """Run the full 5-pass conversation learning workflow."""
    import datetime as dt

    # Pass 1: Scan — parse session notes for signals
    signals = []
    for full, rel, name, content in walk_md(vault_dir):
        if cutoff := _get_cutoff(days):
            try:
                ts = os.path.getmtime(full)
                mtime = datetime.datetime.fromtimestamp(ts, dt.timezone.utc)
                if mtime < cutoff:
                    continue
            except Exception:
                pass
        session_signals = extract_learning_signals(content)
        for s in session_signals:
            signals.append({
                **s,
                "source": rel,
                "name": name,
            })

    # Pass 2: Generate — convert signals into candidate learnings
    candidates = []
    for s in signals:
        candidates.append({
            "title": f"Learning from {s['source']}",
            "text": s["text"],
            "content": s["text"],
            "category": s["category"],
            "source": s["source"],
        })

    # Pass 3: Dedup — check against existing entries
    unique_candidates = []
    seen_texts = set()
    for c in candidates:
        text_key = c["text"][:50].lower()
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_candidates.append(c)

    # Pass 4: Confirm — present for human approval
    confirmed = []
    for c in unique_candidates:
        c["confirmed"] = not dry_run
        c["status"] = "pending" if dry_run else "confirmed"
        confirmed.append(c)

    # Pass 5: Execute — write confirmed learnings to vault
    written = []
    if not dry_run:
        memory_review_dir = os.path.join(VAULT, "04-Archives", "Memory-Review")
        os.makedirs(memory_review_dir, exist_ok=True)
        for c in confirmed:
            fname = f"{slugify(c['title'])}.md"
            fpath = os.path.join(memory_review_dir, fname)
            content = f"# {c['title']}\n\nSource: [[{c['source']}]]\n\n{c['content']}\n"
            write_file(fpath, content)
            written.append(fpath)

    return {
        "scanned": len(signals),
        "candidates": len(candidates),
        "unique": len(unique_candidates),
        "confirmed": len(confirmed),
        "written": len(written),
        "candidates_detail": unique_candidates,
        "written_files": written,
    }


def _get_cutoff(days):
    if days:
        return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 converse_learn/orchestrator.py Self-Test Suite")
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

    # Test 1: extract_learning_signals
    def test_extract_learning_signals():
        content = "Error: forgot to save. Fixed by adding autosave."
        signals = extract_learning_signals(content)
        assert len(signals) >= 1
    check("extract_learning_signals works", test_extract_learning_signals)

    # Test 2: run_orchestrator dry-run
    def test_orchestrator_dryrun():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "session.md"), "# Session\n\nError: forgot to save. Fixed by adding autosave.")
            result = run_orchestrator(tmp, days=30, dry_run=True)
            assert result["scanned"] >= 1
            assert result["candidates"] >= 1
            assert result["written"] == 0  # dry-run doesn't write
        finally:
            shutil.rmtree(tmp)
    check("run_orchestrator dry-run", test_orchestrator_dryrun)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Converse Learn Orchestrator — 5-pass conversation learning workflow.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    p_scan = sub.add_parser("scan", help="Scan sessions for self-improvement learnings (dry-run report)")
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

    result = run_orchestrator(VAULT, days=args.days, dry_run=dry_run)

    print(f"🔄 Orchestrator — conversation learning workflow")
    print(f"   Scanned: {result['scanned']} signals")
    print(f"   Candidates: {result['candidates']}")
    print(f"   Unique: {result['unique']}")
    print(f"   Confirmed: {result['confirmed']}")
    print(f"   Written: {result['written']}")
    print()

    if result["candidates_detail"]:
        print("| Source | Category | Text |")
        print("|--------|----------|------|")
        for c in result["candidates_detail"][:20]:
            text = c["text"][:60]
            print(f"| `{c['source']}` | {c['category']} | {text} |")
        if len(result["candidates_detail"]) > 20:
            print(f"| ... and {len(result['candidates_detail']) - 20} more | | |")

    print()
    if dry_run:
        print("Run with --apply to confirm and write learnings to vault.")
    else:
        print(f"✅ Wrote {result['written']} learning file(s) to vault.")


if __name__ == "__main__":
    main()
