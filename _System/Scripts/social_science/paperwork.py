#!/usr/bin/env python3
"""
Hermes Brain — Social Science Sub-Skill: paperwork (social_science/paperwork.py)

Academic paper processing, citation management, bibliography formatting,
and paper metadata tracking for social science research.

Part of the social_science multi-harness agent skill suite (issue #24).

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python social_science/paperwork.py --vault <path> scan --days 30
  python social_science/paperwork.py --vault <path> scan --days 30 --apply
  python social_science/paperwork.py --vault <path> --test
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
PAPERWORK_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT, PAPERWORK_DIR
    VAULT = os.path.abspath(vault_path)
    PAPERWORK_DIR = os.path.join(VAULT, "04-Archives", "Social-Science", "Paperwork")


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


CITATION_RE = re.compile(
    r"\(([A-Z][A-Za-z\-]+(?:\s+et\s+al\.)?,\s*\d{4}[a-z]?)\)"
)
BRACKET_CITE_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
DOI_RE = re.compile(r"\b(?:DOI|doi)\s*:?\s*(10\.\d+/[^\s]+)", re.I)
URL_RE = re.compile(r"https?://[^\s\)]+", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------
def extract_citations(text):
    """Extract parenthetical citations: (Author, 2024), (Smith et al., 2023a)."""
    citations = []
    for m in CITATION_RE.finditer(text):
        full = m.group(1)
        # Split author and year
        parts = full.rsplit(",", 1)
        author = parts[0].strip() if len(parts) > 1 else full
        year = parts[1].strip() if len(parts) > 1 else ""
        citations.append({
            "author": author,
            "year": year,
            "full": full,
        })
    return citations


def extract_bracket_citations(text):
    """Extract bracket citations: [1], [1, 2, 3]."""
    citations = []
    for m in BRACKET_CITE_RE.finditer(text):
        nums = [int(n.strip()) for n in m.group(1).split(",")]
        citations.append({
            "numbers": nums,
        })
    return citations


def extract_dois(text):
    """Extract DOI references."""
    return DOI_RE.findall(text)


def extract_urls(text):
    """Extract URL references."""
    return URL_RE.findall(text)


# ---------------------------------------------------------------------------
# Paper metadata
# ---------------------------------------------------------------------------
def extract_paper_metadata(text, path):
    """Extract title, authors, year, venue from a paper note."""
    # Title: first H1 heading
    title_match = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else os.path.basename(path)

    # Authors: look for "By" or "Authors:" patterns
    author_match = re.search(
        r"(?:by|authors?):?\s*(.+)", text, re.I | re.M
    )
    authors = author_match.group(1).strip() if author_match else ""

    # Year: first 4-digit year that looks like a publication year
    years = re.findall(r"\b(?:19|20)\d{2}\b", text)
    year = years[0] if years else ""

    # Venue: look for journal/conference indicators
    venue_match = re.search(
        r"(?:published in|journal|conference|proceedings):\s*(.+)", text, re.I | re.M
    )
    venue = venue_match.group(1).strip() if venue_match else ""

    return {
        "path": path,
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
    }


def format_bibliography_entry(meta, style="apa"):
    """Format a bibliography entry in APA or simple style."""
    if style == "apa":
        authors = meta["authors"] or "Unknown Author"
        year = meta["year"] or "n.d."
        title = meta["title"] or "Untitled"
        venue = meta["venue"] or ""
        return f"{authors} ({year}). {title}. {venue}".strip()
    else:
        return f"{meta['title']} — {meta['authors']} ({meta['year']})"


# ---------------------------------------------------------------------------
# Scan vault notes for paperwork
# ---------------------------------------------------------------------------
def scan_paperwork(vault_dir, days=30):
    """Scan vault notes and extract paper metadata and citations."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    papers = []
    all_citations = []
    all_dois = []
    all_urls = []

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

        meta = extract_paper_metadata(content, rel)
        cites = extract_citations(content)
        bracket_cites = extract_bracket_citations(content)
        dois = extract_dois(content)
        urls = extract_urls(content)

        all_citations.extend(cites)
        all_dois.extend(dois)
        all_urls.extend(urls)

        papers.append({
            **meta,
            "citations": cites,
            "bracket_citations": bracket_cites,
            "dois": dois,
            "urls": urls,
            "citation_count": len(cites) + len(bracket_cites),
        })

    # Sort by citation count (most cited first)
    papers.sort(key=lambda p: p["citation_count"], reverse=True)
    return {
        "papers": papers,
        "all_citations": all_citations,
        "all_dois": list(dict.fromkeys(all_dois)),
        "all_urls": list(dict.fromkeys(all_urls)),
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def paperwork_to_markdown(result, days=30):
    papers = result["papers"]
    lines = [
        f"# Paperwork Report — Academic Paper Processing",
        f"Generated: {datetime.datetime.now().isoformat()}",
        f"Window: last {days} days",
        f"Papers analyzed: {len(papers)}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Total papers**: {len(papers)}",
        f"- **Total citations found**: {len(result['all_citations'])}",
        f"- **Total DOIs**: {len(result['all_dois'])}",
        f"- **Total URLs**: {len(result['all_urls'])}",
        "",
        "---",
        "",
        "## Papers (sorted by citation count)",
        "",
        "| Path | Title | Year | Citations | DOIs | URLs |",
        "|------|-------|------|-----------|------|------|",
    ]

    for p in papers[:30]:
        title = p["title"][:60]
        lines.append(
            f"| `{p['path']}` | {title} | {p['year']} | {p['citation_count']} | "
            f"{len(p['dois'])} | {len(p['urls'])} |"
        )
    if len(papers) > 30:
        lines.append(f"| ... and {len(papers) - 30} more papers | | | | | |")
    lines.append("")

    if result["all_dois"]:
        lines.append("## DOIs Found")
        for doi in result["all_dois"][:20]:
            lines.append(f"- {doi}")
        lines.append("")

    if result["all_urls"]:
        lines.append("## URLs Found")
        for url in result["all_urls"][:20]:
            lines.append(f"- {url}")
        lines.append("")

    lines.append("## Bibliography (APA style)")
    for p in papers[:20]:
        entry = format_bibliography_entry(p, style="apa")
        lines.append(f"- {entry}")
    lines.append("")

    lines.append("## Next Steps")
    lines.append("- Review papers with missing metadata (title, year, venue)")
    lines.append("- Cross-reference citations with bibliography")
    lines.append("- Add missing DOIs for paper lookup")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 social_science/paperwork.py Self-Test Suite")
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

    # Test 1: extract_citations
    def test_extract_citations():
        text = "This was shown by (Smith, 2024) and (Jones et al., 2023a)."
        cites = extract_citations(text)
        assert len(cites) == 2
        assert cites[0]["author"] == "Smith"
        assert cites[0]["year"] == "2024"
        assert cites[1]["author"] == "Jones et al."
    check("extract_citations extracts parenthetical citations", test_extract_citations)

    # Test 2: extract_bracket_citations
    def test_extract_bracket_cites():
        text = "See [1] and [1, 2, 3] for details."
        cites = extract_bracket_citations(text)
        assert len(cites) == 2
        assert cites[0]["numbers"] == [1]
        assert cites[1]["numbers"] == [1, 2, 3]
    check("extract_bracket_citations extracts bracket citations", test_extract_bracket_cites)

    # Test 3: extract_paper_metadata
    def test_extract_metadata():
        text = "# The Impact of Social Media\n\nBy Jane Doe and John Smith\n\nPublished in Journal of Social Science, 2024.\n\nDOI: 10.1234/example"
        meta = extract_paper_metadata(text, "papers/social-media.md")
        assert meta["title"] == "The Impact of Social Media"
        assert "Jane Doe" in meta["authors"]
        assert meta["year"] == "2024"
    check("extract_paper_metadata extracts title/authors/year", test_extract_metadata)

    # Test 4: format_bibliography_entry
    def test_format_bibliography():
        meta = {
            "title": "Test Paper",
            "authors": "Author, A.",
            "year": "2024",
            "venue": "Test Journal",
        }
        entry = format_bibliography_entry(meta, style="apa")
        assert "Author, A." in entry
        assert "2024" in entry
        assert "Test Paper" in entry
    check("format_bibliography_entry formats APA style", test_format_bibliography)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Social Science — Paperwork (academic paper processing).",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    p_scan = sub.add_parser("scan", help="Scan vault notes for paper metadata and citations (dry-run report)")
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

    print(f"📄 Scanning vault paperwork (last {args.days} days)...\n")

    result = scan_paperwork(VAULT, days=args.days)
    report = paperwork_to_markdown(result, days=args.days)
    print(report)

    if dry_run:
        print(f"\n📄 Run with --apply to write report to {PAPERWORK_DIR}/")
    else:
        os.makedirs(PAPERWORK_DIR, exist_ok=True)
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(PAPERWORK_DIR, f"paperwork-{date_str}.md")
        write_file(path, report)
        print(f"\n📄 Report written to {path}")


if __name__ == "__main__":
    main()
