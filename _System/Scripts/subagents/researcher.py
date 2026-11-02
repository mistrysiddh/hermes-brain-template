#!/usr/bin/env python3
"""
Hermes Brain — Researcher Sub-Skill (subagents/researcher.py)

Performs on-demand deep research on a topic across vault notes,
finding related content and surfacing relevant connections.
Part of the subagents multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  python subagents/researcher.py --vault <path> research --topic <topic>
  python subagents/researcher.py --vault <path> research --topic <topic> --days 30

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
# Researcher — deep research on a topic across vault notes
# ---------------------------------------------------------------------------
def run_researcher(vault_dir, topic, days=None):
    """Research a topic across vault notes — find all related notes."""
    topic_tokens = tokenize(topic)
    results = []
    import datetime as dt
    cutoff = None
    if days:
        cutoff = datetime.datetime.now(dt.timezone.utc) - datetime.timedelta(days=days)

    for full, rel, name, content in walk_md(vault_dir):
        if cutoff:
            try:
                ts = os.path.getmtime(full)
                mtime = datetime.datetime.fromtimestamp(ts, dt.timezone.utc)
                if mtime < cutoff:
                    continue
            except Exception:
                pass

        sim = jaccard(topic_tokens, tokenize(content))
        if sim > 0:
            # Find matching context
            context = ""
            for line in content.splitlines():
                if any(t in line.lower() for t in topic_tokens):
                    context = line.strip()[:200]
                    break
            results.append({
                "rel_path": rel,
                "name": name,
                "similarity": round(sim, 3),
                "content_preview": content[:200],
                "context": context,
            })

    results.sort(key=lambda x: -x["similarity"])
    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 subagents/researcher.py Self-Test Suite")
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

    # Test 1: run_researcher finds topic
    def test_researcher():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "ai.md"), "# AI\n\nArtificial intelligence is great.")
            write_file(os.path.join(tmp, "cooking.md"), "# Cooking\n\nHow to make pasta.")
            results = run_researcher(tmp, "artificial intelligence")
            assert len(results) >= 1
            assert results[0]["name"] == "ai"
        finally:
            shutil.rmtree(tmp)
    check("researcher finds topic", test_researcher)

    # Test 2: run_researcher filters by days
    def test_researcher_days():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            import os
            write_file(os.path.join(tmp, "recent.md"), "# Recent\n\nAI content.")
            old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=200)).timestamp()
            os.utime(os.path.join(tmp, "recent.md"), (old_time, old_time))
            results = run_researcher(tmp, "AI", days=30)
            assert len(results) == 0  # Too old
        finally:
            shutil.rmtree(tmp)
    check("researcher filters by days", test_researcher_days)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Researcher — deep research on a topic across vault notes.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_research = sub.add_parser("research", help="Research a topic across vault notes")
    p_research.add_argument("--topic", required=True, help="Topic to research")
    p_research.add_argument("--days", type=int, help="Only include notes modified within N days")

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

    if args.command and args.command != "research":
        print(f"Error: Unknown command '{args.command}'. Use 'research'.", file=sys.stderr)
        sys.exit(1)

    results = run_researcher(VAULT, args.topic, days=args.days)

    print(f"🔍 Researcher — topic: {args.topic}")
    print(f"   Found {len(results)} related note(s)")
    print()

    if not results:
        print("✅ No related notes found.")
        return

    print("| Note | Similarity | Context |")
    print("|------|------------|---------|")
    for r in results[:30]:
        ctx = r["context"][:80] if r["context"] else "—"
        print(f"| `{r['rel_path']}` | {r['similarity']} | {ctx} |")

    if len(results) > 30:
        print(f"| ... and {len(results) - 30} more | | |")

    print()


if __name__ == "__main__":
    main()
