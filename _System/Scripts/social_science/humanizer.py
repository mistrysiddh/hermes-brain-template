#!/usr/bin/env python3
"""
Hermes Brain — Social Science Sub-Skill: humanizer (social_science/humanizer.py)

Prose routing, writing pattern diagnosis, sectional chunking, writing habit
study, Turnitin mitigation, research integrity, and evidence preservation
for social science and academic writing.

Part of the social_science multi-harness agent skill suite (issue #24).

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python social_science/humanizer.py --vault <path> scan --days 30
  python social_science/humanizer.py --vault <path> scan --days 30 --apply
  python social_science/humanizer.py --vault <path> --test
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
HUMANIZER_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT, HUMANIZER_DIR
    VAULT = os.path.abspath(vault_path)
    HUMANIZER_DIR = os.path.join(VAULT, "04-Archives", "Social-Science", "Humanizer")


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


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.M)
PARAGRAPH_RE = re.compile(r"\n\s*\n")
SENTENCE_RE = re.compile(r"[.!?]+[\s]+|[.!?]+$")


# ---------------------------------------------------------------------------
# Prose analysis
# ---------------------------------------------------------------------------
def count_words(text):
    return len(re.findall(r"\b\w[\w'-]*\b", text))


def count_sentences(text):
    parts = re.split(SENTENCE_RE, text.strip())
    parts = [p for p in parts if p.strip()]
    return len(parts) if parts else 1


def count_syllables(word):
    word = word.lower().strip(".,!?;:\"'()[]{}")
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    word = re.sub(r"e$", "", word)
    groups = re.findall(r"[aeiouy]+", word)
    return max(1, len(groups))


def avg_sentence_length(text):
    words = count_words(text)
    sentences = count_sentences(text)
    return round(words / sentences, 1) if sentences > 0 else 0


def avg_syllables_per_word(text):
    words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]*\b", text.lower())
    if not words:
        return 0.0
    return round(sum(count_syllables(w) for w in words) / len(words), 2)


# AI-like writing pattern indicators
AI_PATTERN_RE = re.compile(
    r"\b(?:furthermore|moreover|in addition|consequently|nevertheless|"
    r"nonetheless|additionally|importantly|crucially|significantly|"
    r"it is worth noting|it is important to|it should be noted|"
    r"in conclusion|to summarize|overall|ultimately|in essence|"
    r"delve|tapestry|testament|beacon|leverage|robust|comprehensive|"
    r"seamless|elevate|foster|navigate|pivotal|intricate)\b",
    re.I,
)


def detect_ai_patterns(text):
    """Detect AI-like writing patterns (for Turnitin mitigation / integrity)."""
    matches = AI_PATTERN_RE.findall(text)
    return {
        "count": len(matches),
        "patterns": matches[:10],
        "density_per_100_words": round(len(matches) / max(1, count_words(text)) * 100, 2),
    }


# ---------------------------------------------------------------------------
# Sectional chunking
# ---------------------------------------------------------------------------
def section_chunks(text, max_words=300):
    """Split text into sectional chunks by headings, respecting max words."""
    chunks = []
    lines = text.split("\n")
    current_chunk = []
    current_words = 0
    current_heading = None

    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match:
            # Flush previous chunk
            if current_chunk:
                chunks.append({
                    "heading": current_heading,
                    "content": "\n".join(current_chunk).strip(),
                    "word_count": current_words,
                })
            current_heading = heading_match.group(2).strip()
            current_chunk = [line]
            current_words = count_words(line)
        else:
            line_words = count_words(line)
            if current_words + line_words > max_words and current_chunk:
                chunks.append({
                    "heading": current_heading,
                    "content": "\n".join(current_chunk).strip(),
                    "word_count": current_words,
                })
                current_chunk = [line]
                current_words = line_words
            else:
                current_chunk.append(line)
                current_words += line_words

    if current_chunk:
        chunks.append({
            "heading": current_heading,
            "content": "\n".join(current_chunk).strip(),
            "word_count": current_words,
        })

    return chunks


# ---------------------------------------------------------------------------
# Writing habit analysis
# ---------------------------------------------------------------------------
def analyze_writing_habits(text):
    """Analyze writing habits: sentence length, syllable density, passive voice, etc."""
    words = count_words(text)
    sentences = count_sentences(text)
    asl = avg_sentence_length(text)
    asw = avg_syllables_per_word(text)

    # Passive voice heuristic: "was/were/been/being + past participle"
    passive_re = re.compile(
        r"\b(?:was|were|been|being|is|are|am|be)\s+\w+ed\b", re.I
    )
    passive_count = len(passive_re.findall(text))

    # First-person usage
    first_person_re = re.compile(r"\b(?:i|me|my|mine|we|us|our|ours)\b", re.I)
    first_person_count = len(first_person_re.findall(text))

    return {
        "words": words,
        "sentences": sentences,
        "avg_sentence_length": asl,
        "avg_syllables_per_word": asw,
        "passive_voice_count": passive_count,
        "passive_voice_pct": round(passive_count / max(1, sentences) * 100, 1),
        "first_person_count": first_person_count,
        "first_person_pct": round(first_person_count / max(1, words) * 100, 1),
    }


# ---------------------------------------------------------------------------
# Research integrity / evidence preservation
# ---------------------------------------------------------------------------
def detect_citations(text):
    """Detect citation patterns: [1], (Author, 2024), etc."""
    bracket_cites = re.findall(r"\[(\d+(?:,\s*\d+)*)\]", text)
    paren_cites = re.findall(
        r"\(([A-Z][a-zA-Z\-]+(?:\s+et\s+al\.)?,\s*\d{4}[a-z]?)\)", text
    )
    return {
        "bracket_citations": len(bracket_cites),
        "parenthetical_citations": len(paren_cites),
        "total": len(bracket_cites) + len(paren_cites),
    }


def detect_claims_without_evidence(text):
    """Flag strong claims that lack nearby citations."""
    claim_indicators = re.compile(
        r"\b(?:proven|demonstrated|established|confirmed|shows|indicates|"
        r"reveals|suggests|implies|confirms|validates)\b", re.I
    )
    sentences = re.split(SENTENCE_RE, text.strip())
    flagged = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if claim_indicators.search(s) and not re.search(r"\[\d+\]|\([^)]*,\s*\d{4}\)", s):
            flagged.append(s[:120])
    return {
        "claims_without_citation": len(flagged),
        "examples": flagged[:5],
    }


# ---------------------------------------------------------------------------
# Scan vault notes
# ---------------------------------------------------------------------------
def scan_humanizer(vault_dir, days=30):
    """Scan vault notes and analyze writing patterns."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    results = []

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

        habits = analyze_writing_habits(content)
        ai_patterns = detect_ai_patterns(content)
        citations = detect_citations(content)
        evidence = detect_claims_without_evidence(content)
        chunks = section_chunks(content, max_words=300)

        results.append({
            "path": rel,
            "name": name,
            "words": habits["words"],
            "habits": habits,
            "ai_patterns": ai_patterns,
            "citations": citations,
            "evidence": evidence,
            "chunks": len(chunks),
            "chunk_details": chunks[:5],
        })

    # Sort by AI pattern density (highest first = most needs humanizing)
    results.sort(key=lambda r: r["ai_patterns"]["density_per_100_words"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def humanizer_to_markdown(results, days=30):
    lines = [
        f"# Humanizer Report — Writing Pattern Analysis",
        f"Generated: {datetime.datetime.now().isoformat()}",
        f"Window: last {days} days",
        f"Notes analyzed: {len(results)}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Notes with AI-like patterns**: {sum(1 for r in results if r['ai_patterns']['count'] > 0)}",
        f"- **Notes missing citations for claims**: {sum(1 for r in results if r['evidence']['claims_without_citation'] > 0)}",
        f"- **Total chunks created**: {sum(r['chunks'] for r in results)}",
        "",
        "---",
        "",
        "## Results (sorted by AI pattern density — highest first)",
        "",
        "| Path | Words | AI Patterns | AI Density | Citations | Claims w/o Cite | Chunks |",
        "|------|-------|-------------|------------|-----------|-----------------|--------|",
    ]

    for r in results[:30]:
        lines.append(
            f"| `{r['path']}` | {r['words']} | {r['ai_patterns']['count']} | "
            f"{r['ai_patterns']['density_per_100_words']} | {r['citations']['total']} | "
            f"{r['evidence']['claims_without_citation']} | {r['chunks']} |"
        )
    if len(results) > 30:
        lines.append(f"| ... and {len(results) - 30} more notes | | | | | | |")
    lines.append("")

    lines.append("## Writing Habit Averages")
    if results:
        avg_asl = sum(r["habits"]["avg_sentence_length"] for r in results) / len(results)
        avg_asw = sum(r["habits"]["avg_syllables_per_word"] for r in results) / len(results)
        avg_passive = sum(r["habits"]["passive_voice_pct"] for r in results) / len(results)
        lines.append(f"- **Avg sentence length**: {avg_asl:.1f} words")
        lines.append(f"- **Avg syllables per word**: {avg_asw:.2f}")
        lines.append(f"- **Avg passive voice %**: {avg_passive:.1f}%")
    lines.append("")

    lines.append("## Recommendations")
    lines.append("- Review notes with high AI pattern density for Turnitin mitigation")
    lines.append("- Add citations to claims without evidence")
    lines.append("- Break long sections into smaller chunks for readability")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 social_science/humanizer.py Self-Test Suite")
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

    # Test 1: count_words
    def test_count_words():
        assert count_words("Hello world") == 2
        assert count_words("") == 0
        assert count_words("The cat's toy.") == 3
    check("count_words counts correctly", test_count_words)

    # Test 2: detect_ai_patterns
    def test_ai_patterns():
        text = "Furthermore, it is worth noting that this is a robust and comprehensive approach."
        result = detect_ai_patterns(text)
        assert result["count"] > 0
        assert result["density_per_100_words"] >= 0
    check("detect_ai_patterns finds AI-like phrases", test_ai_patterns)

    # Test 3: section_chunks
    def test_section_chunks():
        text = "# Heading 1\n\nSome content here.\n\n# Heading 2\n\nMore content here that is longer."
        chunks = section_chunks(text, max_words=100)
        assert len(chunks) >= 1
        assert chunks[0]["heading"] == "Heading 1"
    check("section_chunks splits by heading", test_section_chunks)

    # Test 4: analyze_writing_habits
    def test_writing_habits():
        text = "The cat sat on the mat. It was a warm sunny day."
        habits = analyze_writing_habits(text)
        assert habits["words"] > 0
        assert habits["sentences"] >= 1
        assert "avg_sentence_length" in habits
    check("analyze_writing_habits computes metrics", test_writing_habits)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Social Science — Humanizer (writing pattern analysis).",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    p_scan = sub.add_parser("scan", help="Scan vault notes for writing patterns (dry-run report)")
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

    print(f"🔍 Scanning vault writing patterns (last {args.days} days)...\n")

    results = scan_humanizer(VAULT, days=args.days)
    report = humanizer_to_markdown(results, days=args.days)
    print(report)

    if dry_run:
        print(f"\n📄 Run with --apply to write report to {HUMANIZER_DIR}/")
    else:
        os.makedirs(HUMANIZER_DIR, exist_ok=True)
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(HUMANIZER_DIR, f"humanizer-{date_str}.md")
        write_file(path, report)
        print(f"\n📄 Report written to {path}")


if __name__ == "__main__":
    main()
