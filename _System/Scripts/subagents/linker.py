#!/usr/bin/env python3
"""
Hermes Brain — Linker Sub-Skill (subagents/linker.py)

Finds and adds missing connections between notes in the vault.
Part of the subagents multi-harness agent skill suite.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  python subagents/linker.py --vault <path> scan --threshold 0.6
  python subagents/linker.py --vault <path> scan --apply

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


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


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
# Linker — find missing links between related notes
# ---------------------------------------------------------------------------
def run_linker(vault_dir, threshold=0.6, dry_run=True):
    """Find notes that share topics but aren't linked, suggest links."""
    notes = []
    for full, rel, name, content in walk_md(vault_dir):
        existing_links = set()
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip().split("|")[0].strip()
            existing_links.add(target)
        notes.append({
            "path": full,
            "rel_path": rel,
            "name": name,
            "content": content,
            "tokens": tokenize(content),
            "existing_links": existing_links,
        })

    suggestions = []
    for i in range(len(notes)):
        for j in range(i + 1, len(notes)):
            a, b = notes[i], notes[j]
            sim = jaccard(a["tokens"], b["tokens"])
            if sim < threshold:
                continue
            # Skip if already linked
            if b["name"] in a["existing_links"] or a["name"] in b["existing_links"]:
                continue
            suggestions.append({
                "source": a["rel_path"],
                "target": b["rel_path"],
                "similarity": round(sim, 3),
                "action": "suggest_link",
                "applied": False,
                "reason": "dry-run preview" if dry_run else "linked",
            })

            if not dry_run:
                # Add link to source note
                link_text = f"\n\nSee also [[{b['rel_path']}|{b['name']}]]\n"
                with open(a["path"], "a", encoding="utf-8") as f:
                    f.write(link_text)
                suggestions[-1]["applied"] = True
                suggestions[-1]["reason"] = "linked"

    return suggestions


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 subagents/linker.py Self-Test Suite")
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

    # Test 1: tokenize
    def test_tokenize():
        assert "hello" in tokenize("Hello, world!")
        assert "world" in tokenize("Hello, world!")
        assert len(tokenize("")) == 0
    check("tokenize works correctly", test_tokenize)

    # Test 2: jaccard similarity
    def test_jaccard():
        assert jaccard(set(), set()) == 0.0
        assert jaccard({"a", "b"}, {"a", "b"}) == 1.0
        assert jaccard({"a", "b"}, {"c", "d"}) == 0.0
    check("jaccard similarity correct", test_jaccard)

    # Test 3: run_linker finds missing links
    def test_linker():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# Note A\n\nContent about AI.")
            write_file(os.path.join(tmp, "b.md"), "# Note B\n\nContent about AI and machine learning.")
            results = run_linker(tmp, dry_run=True, threshold=0.3)
            ai_links = [r for r in results if "a.md" in r["source"] and "b.md" in r["target"]]
            assert len(ai_links) >= 1
        finally:
            shutil.rmtree(tmp)
    check("linker finds missing links", test_linker)

    # Test 4: run_linker dry-run does not modify
    def test_linker_dryrun():
        tmp = __import__("tempfile").mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# Note A\n\nContent about AI.")
            write_file(os.path.join(tmp, "b.md"), "# Note B\n\nContent about AI.")
            results = run_linker(tmp, dry_run=True, threshold=0.5)
            for r in results:
                assert r["applied"] is False
            # Verify no file was modified
            content = read_file(os.path.join(tmp, "a.md"))
            assert "[[b.md|b]]" not in content
        finally:
            shutil.rmtree(tmp)
    check("linker dry-run does not modify", test_linker_dryrun)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Linker — find missing links between related notes.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--threshold", type=float, default=0.6, help="Similarity threshold 0-1 (default: 0.6)")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("scan", help="Scan vault for missing links (dry-run report)")
    parser.add_argument("--apply", action="store_true", help="Apply links (overrides --dry-run)")
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

    results = run_linker(VAULT, dry_run=dry_run, threshold=args.threshold)

    print(f"🔗 Linker — scanning vault for missing links")
    print(f"   Found {len(results)} suggestion(s)")
    print()

    if not results:
        print("✅ No missing links found.")
        return

    print("| Source | Target | Similarity |")
    print("|--------|--------|------------|")
    for r in results:
        print(f"| `{r['source']}` | `{r['target']}` | {r['similarity']} |")

    print()
    if dry_run:
        print("Run with --apply to add the missing links above.")
    else:
        print(f"✅ Added {len(results)} link(s).")


if __name__ == "__main__":
    main()
