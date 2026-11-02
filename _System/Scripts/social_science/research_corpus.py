#!/usr/bin/env python3
"""
Hermes Brain — Social Science Sub-Skill: research_corpus (social_science/research_corpus.py)

Research super-corpus automation: aggregate research sources, build corpus
index, track research progress, and manage reading + contemplation workflows.

Part of the social_science multi-harness agent skill suite (issue #24).

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python social_science/research_corpus.py --vault <path> scan --days 30
  python social_science/research_corpus.py --vault <path> scan --days 30 --apply
  python social_science/research_corpus.py --vault <path> --test
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
CORPUS_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT, CORPUS_DIR
    VAULT = os.path.abspath(vault_path)
    CORPUS_DIR = os.path.join(VAULT, "04-Archives", "Social-Science", "Research-Corpus")


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
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash", ".sota"}
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


TAG_RE = re.compile(r"(?:^|\s)#([\w\-/]+)", re.M)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SOURCE_RE = re.compile(
    r"(?:source|source:\s*|source url|url:)\s*(https?://[^\s\)]+)", re.I
)


# ---------------------------------------------------------------------------
# Research source detection
# ---------------------------------------------------------------------------
def detect_research_sources(text):
    """Detect research sources: URLs, DOIs, citations, references."""
    sources = {
        "urls": [],
        "citations": [],
        "references": [],
    }

    # URLs
    url_matches = re.findall(r"https?://[^\s\)]+", text)
    sources["urls"] = url_matches[:20]

    # Parenthetical citations: (Author, 2024)
    cit_matches = re.findall(
        r"\(([A-Z][A-Za-z\-]+(?:\s+et\s+al\.)?,\s*\d{4}[a-z]?)\)", text
    )
    sources["citations"] = cit_matches[:20]

    # References section: "## References" or "References:"
    ref_section = re.split(
        r"##+\s+References?\s*|\nReferences?:", text, maxsplit=1, flags=re.I
    )
    if len(ref_section) > 1:
        ref_text = ref_section[1]
        ref_items = re.findall(r"[-*]\s+(.+)", ref_text)
        sources["references"] = ref_items[:20]

    return sources


def extract_tags(text):
    """Extract tags from content."""
    return TAG_RE.findall(text)


def count_wikilinks(text):
    """Count wikilinks in content."""
    return len(WIKILINK_RE.findall(text))


# ---------------------------------------------------------------------------
# Corpus index
# ---------------------------------------------------------------------------
def build_corpus_index(vault_dir, days=30):
    """Build a research corpus index from vault notes."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    index = {
        "notes": [],
        "tags": {},
        "sources": [],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    for full, rel, name, content in walk_md(vault_dir):
        try:
            mtime = os.path.getmtime(full)
            mtime_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
            if mtime_dt < cutoff:
                continue
        except Exception:
            pass

        if not content.strip():
            continue

        tags = extract_tags(content)
        sources = detect_research_sources(content)
        wikilinks = count_wikilinks(content)
        words = len(re.findall(r"\b\w[\w'-]*\b", content))

        note_entry = {
            "path": rel,
            "name": name,
            "words": words,
            "tags": tags,
            "wikilinks": wikilinks,
            "sources": sources,
        }
        index["notes"].append(note_entry)

        # Aggregate tags
        for tag in tags:
            index["tags"][tag] = index["tags"].get(tag, 0) + 1

        # Aggregate sources
        for url in sources["urls"]:
            index["sources"].append({"type": "url", "value": url, "note": rel})

    # Sort tags by frequency
    index["tags"] = dict(
        sorted(index["tags"].items(), key=lambda x: -x[1])
    )

    return index


# ---------------------------------------------------------------------------
# Reading progress tracking
# ---------------------------------------------------------------------------
def track_reading_progress(index):
    """Track reading progress: read vs unread, tag coverage, source diversity."""
    total = len(index["notes"])
    read_notes = [n for n in index["notes"] if n["wikilinks"] > 0]  # connected = read
    unread = total - len(read_notes)

    tag_count = len(index["tags"])
    source_count = len(index["sources"])

    return {
        "total_notes": total,
        "connected_notes": len(read_notes),
        "unconnected_notes": unread,
        "tag_count": tag_count,
        "source_count": source_count,
        "completion_pct": round(len(read_notes) / max(1, total) * 100, 1),
    }


# ---------------------------------------------------------------------------
# Scan vault for research corpus
# ---------------------------------------------------------------------------
def scan_research_corpus(vault_dir, days=30):
    """Scan vault and build research corpus index."""
    index = build_corpus_index(vault_dir, days=days)
    progress = track_reading_progress(index)
    return {
        "index": index,
        "progress": progress,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def research_corpus_to_markdown(result, days=30):
    index = result["index"]
    progress = result["progress"]
    notes = index["notes"]

    lines = [
        f"# Research Corpus Report",
        f"Generated: {index['generated_at']}",
        f"Window: last {days} days",
        "",
        "---",
        "",
        "## Corpus Overview",
        f"- **Total notes**: {progress['total_notes']}",
        f"- **Connected notes** (have wikilinks): {progress['connected_notes']}",
        f"- **Unconnected notes**: {progress['unconnected_notes']}",
        f"- **Unique tags**: {progress['tag_count']}",
        f"- **Research sources**: {progress['source_count']}",
        f"- **Completion**: {progress['completion_pct']}%",
        "",
        "---",
        "",
        "## Top Tags",
        "",
        "| Tag | Count |",
        "|-----|-------|",
    ]

    for tag, count in list(index["tags"].items())[:20]:
        lines.append(f"| #{tag} | {count} |")
    lines.append("")

    lines.append("## Research Sources")
    if index["sources"]:
        lines.append("")
        lines.append("| Type | Value | Note |")
        lines.append("|------|-------|------|")
        for s in index["sources"][:30]:
            lines.append(f"| {s['type']} | {s['value'][:80]} | {s['note']} |")
    lines.append("")

    lines.append("## Notes by Word Count (largest first)")
    lines.append("")
    lines.append("| Path | Words | Tags | Wikilinks | Sources |")
    lines.append("|------|-------|------|-----------|---------|")
    sorted_notes = sorted(notes, key=lambda n: n["words"], reverse=True)
    for n in sorted_notes[:30]:
        src_count = len(n["sources"]["urls"]) + len(n["sources"]["citations"])
        lines.append(
            f"| `{n['path']}` | {n['words']} | {len(n['tags'])} | "
            f"{n['wikilinks']} | {src_count} |"
        )
    lines.append("")

    lines.append("## Reading + Contemplation Workflow")
    lines.append("")
    lines.append("1. **Read**: Start with unconnected notes (no wikilinks) — these need synthesis")
    lines.append("2. **Contemplate**: Review top tags for theme clusters")
    lines.append("3. **Synthesize**: Connect related notes with wikilinks")
    lines.append("4. **Critique**: Check sources and citations for research integrity")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 social_science/research_corpus.py Self-Test Suite")
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

    # Test 1: detect_research_sources
    def test_detect_sources():
        text = "See https://example.com/paper and (Smith, 2024) for details.\n\n## References\n- Paper One\n- Paper Two"
        sources = detect_research_sources(text)
        assert len(sources["urls"]) >= 1
        assert "Smith, 2024" in sources["citations"]
        assert len(sources["references"]) == 2
    check("detect_research_sources extracts URLs, citations, references", test_detect_sources)

    # Test 2: extract_tags
    def test_extract_tags():
        text = "# Research\n\nThis is about #ai #ml #ai/research and #social-science."
        tags = extract_tags(text)
        assert "ai" in tags
        assert "ml" in tags
        assert "ai/research" in tags
        assert "social-science" in tags
    check("extract_tags extracts tags correctly", test_extract_tags)

    # Test 3: build_corpus_index
    def test_build_corpus_index():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "research.md"),
                       "# Research\n\n#ai #ml\n\nSee https://example.com and (Author, 2024).")
            write_file(os.path.join(tmp, "notes.md"), "# Notes\n\n#social-science")
            index = build_corpus_index(tmp, days=30)
            assert len(index["notes"]) == 2
            assert "ai" in index["tags"]
            assert "ml" in index["tags"]
            assert "social-science" in index["tags"]
        finally:
            shutil.rmtree(tmp)
    check("build_corpus_index builds index with tags", test_build_corpus_index)

    # Test 4: track_reading_progress
    def test_track_progress():
        index = {
            "notes": [
                {"path": "a.md", "wikilinks": 2},
                {"path": "b.md", "wikilinks": 0},
                {"path": "c.md", "wikilinks": 1},
            ],
            "tags": {"ai": 2, "ml": 1},
            "sources": [{"type": "url", "value": "http://x.com", "note": "a.md"}],
            "generated_at": "2026-01-01",
        }
        progress = track_reading_progress(index)
        assert progress["total_notes"] == 3
        assert progress["connected_notes"] == 2
        assert progress["unconnected_notes"] == 1
        assert progress["tag_count"] == 2
        assert progress["source_count"] == 1
    check("track_reading_progress computes metrics", test_track_progress)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Social Science — Research Corpus (research source aggregation).",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    p_scan = sub.add_parser("scan", help="Scan vault notes and build research corpus index (dry-run report)")
    p_scan.add_argument("--days", type=int, default=30, help="Days of notes to scan (default: 30)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="Write report to vault (overrides --dry-run)")
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

    if args.command != "scan":
        print(f"Error: Unknown command '{args.command}'. Use 'scan'.", file=sys.stderr)
        sys.exit(1)

    print(f"📚 Building research corpus index (last {args.days} days)...\n")

    result = scan_research_corpus(VAULT, days=args.days)
    report = research_corpus_to_markdown(result, days=args.days)
    print(report)

    if dry_run:
        print(f"\n📄 Run with --apply to write report to {CORPUS_DIR}/")
    else:
        os.makedirs(CORPUS_DIR, exist_ok=True)
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(CORPUS_DIR, f"research-corpus-{date_str}.md")
        write_file(path, report)
        print(f"\n📄 Report written to {path}")


if __name__ == "__main__":
    main()
