#!/usr/bin/env python3
"""
Hermes Brain — Merge Duplicate Skill (find & merge near-duplicate vault pages).

Scans vault notes, detects near-duplicate content using similarity scoring,
and reports candidate merge pairs for human review. Can also atomize large
notes into smaller modular units (splitting by heading) to keep notes focused.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  merge_duplicate.py scan     Scan vault for near-duplicate pairs (dry-run report)
  merge_duplicate.py atomize  Split a large note into atomic notes by heading
  merge_duplicate.py --test   Built-in self-test suite

Similarity:
  - Jaccard similarity on token sets (title + body)
  - Threshold configurable (default 0.75 = near-duplicate)
  - Only pairs above threshold are reported

Safety:
  - Never auto-deletes or auto-merges — all changes require human approval
  - Each proposed merge gets its own file in 04-Archives/Metrics/duplicates/
  - Divisive/disputed content is flagged, not merged

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
DUP_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, DUP_DIR
    VAULT = os.path.abspath(vault_path)
    DUP_DIR = os.path.join(VAULT, "04-Archives", "Metrics", "duplicates")


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
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-_")
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
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.M)


def tokenize(text):
    """Simple tokenization: lowercase, split on non-alphanumeric."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return set(tokens)


def jaccard(a, b):
    """Jaccard similarity between two token sets."""
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------
def load_notes(vault_dir):
    """Load all notes into memory for comparison."""
    notes = []
    for full, rel, name, content in walk_md(vault_dir):
        # Skip very short notes (likely placeholders or stubs)
        if len(content.strip()) < 20:
            continue
        title_tokens = tokenize(name)
        body_tokens = tokenize(content)
        combined = title_tokens | body_tokens
        notes.append({
            "path": full,
            "rel_path": rel,
            "name": name,
            "content": content,
            "tokens": combined,
            "size": len(content.encode("utf-8")),
            "heading_count": len(HEADING_RE.findall(content)),
        })
    return notes


def find_near_duplicates(notes, threshold=0.75, max_pairs=50):
    """Find pairs of notes with Jaccard similarity above threshold."""
    pairs = []
    n = len(notes)
    for i in range(n):
        for j in range(i + 1, n):
            a = notes[i]
            b = notes[j]
            sim = jaccard(a["tokens"], b["tokens"])
            if sim >= threshold:
                pairs.append({
                    "a": a,
                    "b": b,
                    "similarity": round(sim, 3),
                })
    # Sort by similarity descending
    pairs.sort(key=lambda p: -p["similarity"])
    return pairs[:max_pairs]


def detect_divisive(content):
    """Heuristic: content may be divisive if it contains strong opinion markers."""
    divisive_markers = [
        r"\b(always|never|obviously|clearly|undeniably|absolutely|definitely)\b",
        r"\b(wrong|right|correct|incorrect|bad|good|terrible|amazing)\b",
        r"\b(should|must|ought to|have to)\b",
        r"\b(dispute|controversial|polarizing|divisive)\b",
        r"\b(I think|I believe|in my opinion|personally)\b",
    ]
    score = 0
    for marker in divisive_markers:
        score += len(re.findall(marker, content, re.IGNORECASE))
    return score


def find_large_notes(notes, min_headings=5, min_size_kb=5):
    """Find notes that are candidates for atomization (large, many headings)."""
    large = []
    for note in notes:
        size_kb = note["size"] / 1024
        if note["heading_count"] >= min_headings and size_kb >= min_size_kb:
            large.append({
                **note,
                "size_kb": round(size_kb, 1),
            })
    large.sort(key=lambda n: -n["heading_count"])
    return large


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(pairs, large_notes, threshold, dry_run=True):
    """Generate markdown report of duplicate findings."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Duplicate Detection Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Similarity threshold: {threshold}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Near-duplicate pairs found**: {len(pairs)}",
        f"- **Large notes (atomize candidates)**: {len(large_notes)}",
        "",
        "---",
        "",
    ]

    if not pairs and not large_notes:
        lines.append("## ✅ No near-duplicates or large notes found.")
        return "\n".join(lines)

    if pairs:
        lines.append("## Near-Duplicate Pairs")
        lines.append("")
        lines.append("| Similarity | Note A | Note B | Size A | Size B | Divisive A | Divisive B |")
        lines.append("|------------|--------|--------|--------|--------|------------|------------|")
        for p in pairs:
            a = p["a"]
            b = p["b"]
            div_a = detect_divisive(a["content"])
            div_b = detect_divisive(b["content"])
            div_a_marker = "⚠️" if div_a > 0 else ""
            div_b_marker = "⚠️" if div_b > 0 else ""
            lines.append(
                f"| {p['similarity']} | `{a['rel_path']}` | `{b['rel_path']}` | "
                f"{a['size']} | {b['size']} | {div_a_marker} | {div_b_marker} |"
            )
        lines.append("")
        lines.append("### Divisive content warning")
        lines.append("")
        lines.append(
            "Pairs marked with ⚠️ contain strong opinion markers. "
            "Review carefully before merging — divisive topics may need "
            "separate sub-notes to articulate different perspectives rather than "
            "being merged into a single page."
        )
        lines.append("")

    if large_notes:
        lines.append("## Large Notes (Atomize Candidates)")
        lines.append("")
        lines.append(
            "These notes have many headings and are good candidates for "
            "splitting into smaller, atomic notes."
        )
        lines.append("")
        lines.append("| Note | Headings | Size (KB) |")
        lines.append("|------|----------|-----------|")
        for note in large_notes[:20]:
            lines.append(
                f"| `{note['rel_path']}` | {note['heading_count']} | {note['size_kb']} |"
            )
        if len(large_notes) > 20:
            lines.append(f"| ... and {len(large_notes) - 20} more | | |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. Review near-duplicate pairs above.")
    lines.append("2. For each pair, decide: merge, keep separate, or split into atomic notes.")
    lines.append("3. For divisive content, consider creating separate sub-notes per perspective.")
    lines.append("4. To atomize a large note, run: `merge_duplicate.py --vault <path> atomize --note <rel_path>`")
    lines.append("")
    lines.append("All findings are reported only — nothing is auto-merged or auto-deleted.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Atomize
# ---------------------------------------------------------------------------
def atomize_note(vault_dir, rel_path, dry_run=True):
    """Split a large note into atomic notes by heading."""
    full = os.path.join(vault_dir, rel_path)
    if not os.path.exists(full):
        return f"Error: {rel_path} not found", None

    content = read_file(full)
    if not content.strip():
        return "Error: empty note", None

    # Extract frontmatter
    frontmatter = ""
    body = content
    if content.startswith("---\n"):
        fm_end = content.find("\n---\n", 4)
        if fm_end != -1:
            frontmatter = content[:fm_end + 5]
            body = content[fm_end + 5:]

    # Split by headings - need at least 2 headings to split into multiple notes
    heading_matches = list(HEADING_RE.finditer(body))
    if len(heading_matches) < 2:
        return "Note needs at least 2 headings to atomize into multiple notes", None

    parts = []
    for i, m in enumerate(heading_matches):
        heading = m.group(1).strip()
        start = m.end()
        end = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(body)
        section = body[start:end].strip()
        if not section:
            continue
        parts.append({
            "heading": heading,
            "content": section,
        })

    if not parts:
        return "No splittable sections found", None

    base_name = os.path.splitext(os.path.basename(rel_path))[0]
    base_dir = os.path.dirname(rel_path)
    created = []

    for part in parts:
        new_name = f"{base_name} — {slugify(part['heading'])}"
        new_rel = os.path.join(base_dir, f"{new_name}.md") if base_dir else f"{new_name}.md"
        new_full = os.path.join(vault_dir, new_rel)

        new_content = frontmatter + "\n" if frontmatter else ""
        new_content += f"# {part['heading']}\n\n"
        new_content += f"Source: [[{rel_path}|{base_name}]]\n\n"
        new_content += part["content"] + "\n"

        if dry_run:
            created.append({
                "path": new_rel,
                "heading": part["heading"],
                "size": len(new_content.encode("utf-8")),
                "preview": part["content"][:100],
            })
        else:
            write_file(new_full, new_content)
            created.append({
                "path": new_rel,
                "heading": part["heading"],
                "size": len(new_content.encode("utf-8")),
                "preview": part["content"][:100],
            })

    return None, created


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil
    import traceback

    print("🧪 merge_duplicate.py Self-Test Suite")
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
            traceback.print_exc()
            failed += 1

    # Test 1: jaccard similarity
    def test_jaccard():
        assert jaccard(set(), set()) == 0.0
        assert jaccard({"a", "b"}, {"a", "b"}) == 1.0
        assert jaccard({"a", "b"}, {"c", "d"}) == 0.0
        assert jaccard({"a", "b", "c"}, {"a", "b"}) == 2 / 3
    check("jaccard similarity", test_jaccard)

    # Test 2: tokenize
    def test_tokenize():
        assert "hello" in tokenize("Hello, world!")
        assert "world" in tokenize("Hello, world!")
        assert len(tokenize("")) == 0
    check("tokenize", test_tokenize)

    # Test 3: find_near_duplicates finds similar notes
    def test_duplicates():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "a.md"), "# Python Basics\n\nPython is a programming language used for scripting.")
            write_file(os.path.join(tmp, "b.md"), "# Python Basics\n\nPython is a programming language used for scripting and automation.")
            write_file(os.path.join(tmp, "c.md"), "# Quantum Physics\n\nQuantum mechanics describes nature at the smallest scales.")
            notes = load_notes(tmp)
            pairs = find_near_duplicates(notes, threshold=0.5, max_pairs=10)
            assert len(pairs) >= 1, f"Expected >=1 duplicate pair, got {len(pairs)}"
            assert pairs[0]["a"]["name"] == "a" and pairs[0]["b"]["name"] == "b"
            assert pairs[0]["similarity"] > 0.5
        finally:
            shutil.rmtree(tmp)
    check("find_near_duplicates finds similar notes", test_duplicates)

    # Test 4: detect_divisive
    def test_divisive():
        assert detect_divisive("This is obviously wrong and should never be done.") > 0
        assert detect_divisive("The sky is blue.") == 0
    check("detect_divisive", test_divisive)

    # Test 5: find_large_notes
    def test_large_notes():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            large_content = ("# Big Note\n\n## Section 1\n\nContent one.\n\n## Section 2\n\nContent two.\n\n"
                             "## Section 3\n\nContent three.\n\n## Section 4\n\nContent four.\n\n"
                             "## Section 5\n\nContent five.\n")
            write_file(os.path.join(tmp, "big.md"), large_content)
            write_file(os.path.join(tmp, "small.md"), "# Small\n\nJust a little note.")
            notes = load_notes(tmp)
            large = find_large_notes(notes, min_headings=5, min_size_kb=0.1)
            assert len(large) == 1, f"Expected 1 large note, got {len(large)}"
            assert large[0]["name"] == "big"
        finally:
            shutil.rmtree(tmp)
    check("find_large_notes identifies large notes", test_large_notes)

    # Test 6: atomize splits by heading (dry-run)
    def test_atomize():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            content = ("---\ntitle: \"Test\"\n---\n\n# Big Note\n\n## Section A\n\nContent A here.\n\n"
                       "## Section B\n\nContent B here.\n")
            write_file(os.path.join(tmp, "big.md"), content)
            error, created = atomize_note(tmp, "big.md", dry_run=True)
            assert error is None, f"Expected no error, got {error}"
            assert len(created) == 2, f"Expected 2 created notes, got {len(created)}"
            assert created[0]["heading"] == "Section A"
            assert created[1]["heading"] == "Section B"
        finally:
            shutil.rmtree(tmp)
    check("atomize splits by heading (dry-run)", test_atomize)

    # Test 7: atomize requires 2+ headings
    def test_atomize_single_heading():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "plain.md"), "# Plain\n\nJust content, no subheadings.")
            error, created = atomize_note(tmp, "plain.md", dry_run=True)
            assert error is not None, "Expected error for single-heading note"
            assert created is None
        finally:
            shutil.rmtree(tmp)
    check("atomize requires 2+ headings", test_atomize_single_heading)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Merge Duplicate — find & merge near-duplicate vault pages.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--threshold", type=float, default=0.75, help="Similarity threshold 0-1 (default: 0.75)")
    parser.add_argument("--max-pairs", type=int, default=50, help="Max pairs to report (default: 50)")
    parser.add_argument("--min-headings", type=int, default=5, help="Min headings for atomize candidate (default: 5)")
    parser.add_argument("--min-size-kb", type=float, default=5.0, help="Min size in KB for atomize candidate (default: 5)")
    parser.add_argument("--note", help="Specific note to atomize (rel path from vault root)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true", help="Apply changes with human approval (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("scan", help="Scan vault for near-duplicate pairs (dry-run report)")
    sub.add_parser("atomize", help="Split a large note into atomic notes by heading")
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

    if args.command == "atomize":
        if not args.note:
            print("Error: --note <rel_path> is required for atomize command.", file=sys.stderr)
            sys.exit(1)
        error, created = atomize_note(VAULT, args.note, dry_run=dry_run)
        if error:
            print(f"❌ {error}")
            sys.exit(1)
        if dry_run:
            print(f"📄 Atomize preview (dry-run — {len(created)} notes would be created):")
            for c in created:
                print(f"  - {c['path']} ({c['size']} bytes) — {c['heading']}")
        else:
            print(f"✅ Atomized {args.note} into {len(created)} atomic notes:")
            for c in created:
                print(f"  - {c['path']} ({c['size']} bytes) — {c['heading']}")
        return

    # Default: scan
    print(f"🔍 Scanning vault for near-duplicates (threshold={args.threshold})...\n")
    notes = load_notes(VAULT)
    print(f"📝 Loaded {len(notes)} notes for comparison\n")

    pairs = find_near_duplicates(notes, threshold=args.threshold, max_pairs=args.max_pairs)
    large_notes = find_large_notes(notes, min_headings=args.min_headings, min_size_kb=args.min_size_kb)

    report = generate_report(pairs, large_notes, args.threshold, dry_run=dry_run)
    print(report[:3000])
    if len(report) > 3000:
        print(f"\n... ({len(report) - 3000} more chars)")

    # Save report to vault
    os.makedirs(DUP_DIR, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(DUP_DIR, f"Duplicate-Report-{today}.md")
    write_file(report_path, report)
    print(f"\n📄 Full report saved to {report_path}")


if __name__ == "__main__":
    main()
