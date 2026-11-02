#!/usr/bin/env python3
"""
Hermes Brain — Social Science Sub-Skill: skill_table (social_science/skill_table.py)

Coherent table-of-skills that merges observations from humanizer, paperwork,
and research_corpus into a unified view for reading + contemplation +
synthesis/critique workflows.

Part of the social_science multi-harness agent skill suite (issue #24).

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python social_science/skill_table.py --vault <path> scan --days 30
  python social_science/skill_table.py --vault <path> scan --days 30 --apply
  python social_science/skill_table.py --vault <path> --test
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
SKILL_TABLE_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT, SKILL_TABLE_DIR
    VAULT = os.path.abspath(vault_path)
    SKILL_TABLE_DIR = os.path.join(VAULT, "04-Archives", "Social-Science", "Skill-Table")


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


# ---------------------------------------------------------------------------
# Skill catalog (external social science / research skills from issue #24)
# ---------------------------------------------------------------------------
EXTERNAL_SKILLS = [
    {
        "id": "humanizer",
        "name": "Humanizer",
        "source": "https://github.com/XuyueyangHe/Qualitative-social-science-humanizer",
        "capabilities": [
            "prose routing",
            "writing pattern diagnosis",
            "sectional chunking",
            "writing habits study",
            "Turnitin mitigation",
            "research integrity",
            "evidence preservation",
        ],
        "category": "writing",
    },
    {
        "id": "paperwork",
        "name": "Paperwork",
        "source": "https://github.com/handsomeZR-netizen/social-science-paperwork-skill",
        "alt_source": "https://github.com/fakerqwq/social-science-paper-writing-skill",
        "capabilities": [
            "academic paper processing",
            "citation management",
            "bibliography formatting",
            "paper metadata tracking",
        ],
        "category": "paperwork",
    },
    {
        "id": "research-corpus",
        "name": "Research Corpus",
        "source": "https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills",
        "capabilities": [
            "research source aggregation",
            "corpus index building",
            "reading progress tracking",
            "source diversity analysis",
        ],
        "category": "corpus",
    },
    {
        "id": "superpower-socialscience",
        "name": "Superpower Social Science",
        "source": "https://github.com/ptreezh/superpower-socialscience-skills",
        "capabilities": [
            "social science skill overview",
            "research workflow support",
        ],
        "category": "overview",
    },
    {
        "id": "academic-research",
        "name": "Academic Research Skills",
        "source": "https://github.com/franklee16/academic-research-skills",
        "capabilities": [
            "common academic research skill types",
            "research methodology support",
        ],
        "category": "research",
    },
    {
        "id": "open-science",
        "name": "Open Science Skills",
        "source": "https://github.com/scdenney/open-science-skills",
        "capabilities": [
            "open science practices",
            "reproducible research",
            "open data support",
        ],
        "category": "open-science",
    },
    {
        "id": "claude-academic",
        "name": "Claude Academic Skills",
        "source": "https://github.com/Nero1688/claude-academic-skills",
        "capabilities": [
            "academic skill overview",
            "research flow organization",
        ],
        "category": "overview",
    },
]


def categorize_skill_by_content(text):
    """Categorize a vault note by matching its content to skill categories."""
    text_lower = text.lower()
    scores = {}
    for skill in EXTERNAL_SKILLS:
        score = 0
        for cap in skill["capabilities"]:
            # Check if any capability keyword appears in the text
            cap_words = cap.split()
            for w in cap_words:
                if w in text_lower:
                    score += 1
        if score > 0:
            scores[skill["id"]] = score
    return scores


# ---------------------------------------------------------------------------
# Scan vault for skill mapping
# ---------------------------------------------------------------------------
def scan_skill_table(vault_dir, days=30):
    """Scan vault notes and map them to the coherent skill table."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    skill_notes = {s["id"]: [] for s in EXTERNAL_SKILLS}
    uncategorized = []
    tag_skill_map = {}

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

        scores = categorize_skill_by_content(content)
        tags = TAG_RE.findall(content)
        wikilinks = len(WIKILINK_RE.findall(content))
        words = len(re.findall(r"\b\w[\w'-]*\b", content))

        note_entry = {
            "path": rel,
            "name": name,
            "words": words,
            "tags": tags,
            "wikilinks": wikilinks,
            "skill_scores": scores,
            "matched_skills": list(scores.keys()),
        }

        if scores:
            # Assign to best matching skill
            best_skill = max(scores, key=scores.get)
            skill_notes[best_skill].append(note_entry)
        else:
            uncategorized.append(note_entry)

        # Build tag → skill mapping
        for tag in tags:
            tag_skill_map.setdefault(tag, []).append(rel)

    return {
        "skill_notes": skill_notes,
        "uncategorized": uncategorized,
        "tag_skill_map": tag_skill_map,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Coherent table-of-skills generation
# ---------------------------------------------------------------------------
def generate_skill_table(result):
    """Generate a coherent table-of-skills merging all observations."""
    skill_notes = result["skill_notes"]
    uncategorized = result["uncategorized"]
    tag_skill_map = result["tag_skill_map"]

    skill_map = {s["id"]: s for s in EXTERNAL_SKILLS}

    lines = [
        "# Coherent Table-of-Skills — Social Science & Research",
        f"Generated: {result['generated_at']}",
        "",
        "---",
        "",
        "## Overview",
        "This table merges observations from humanizer, paperwork, and research_corpus "
        "sub-skills into a coherent view for **reading + contemplation + synthesis/critique**.",
        "",
        "| Skill | Category | Capabilities | Vault Notes | Match Score |",
        "|-------|----------|--------------|-------------|-------------|",
    ]

    total_notes = 0
    for skill in EXTERNAL_SKILLS:
        sid = skill["id"]
        notes = skill_notes[sid]
        total_notes += len(notes)
        caps = ", ".join(skill["capabilities"][:3])
        if len(skill["capabilities"]) > 3:
            caps += "..."
        lines.append(
            f"| **{skill['name']}** ({sid}) | {skill['category']} | {caps} | "
            f"{len(notes)} | — |"
        )
    lines.append(f"| **Uncategorized** | — | — | {len(uncategorized)} | — |")
    lines.append("")

    lines.append("## Skill Details")
    for skill in EXTERNAL_SKILLS:
        sid = skill["id"]
        notes = skill_notes[sid]
        lines.append(f"### {skill['name']}")
        lines.append(f"- **Source**: {skill['source']}")
        if skill.get("alt_source"):
            lines.append(f"- **Alt Source**: {skill['alt_source']}")
        lines.append(f"- **Capabilities**: {', '.join(skill['capabilities'])}")
        lines.append(f"- **Vault notes matched**: {len(notes)}")
        if notes:
            lines.append("  - " + "\n  - ".join(f"`{n['path']}` ({n['words']} words)" for n in notes[:5]))
        lines.append("")

    if uncategorized:
        lines.append("## Uncategorized Notes")
        lines.append("")
        lines.append("These notes didn't match any known skill category:")
        for n in uncategorized[:20]:
            lines.append(f"- `{n['path']}` ({n['words']} words, tags: {', '.join(n['tags'])})")
        lines.append("")

    lines.append("## Tag → Skill Mapping")
    lines.append("")
    lines.append("| Tag | Mapped Skills | Note Count |")
    lines.append("|-----|---------------|------------|")
    for tag, note_paths in sorted(tag_skill_map.items(), key=lambda x: -len(x[1]))[:20]:
        # Find which skills this tag's notes map to
        mapped = set()
        for np in note_paths:
            for sid, snotes in skill_notes.items():
                if any(n["path"] == np for n in snotes):
                    mapped.add(skill_map[sid]["name"])
        mapped_str = ", ".join(sorted(mapped)) if mapped else "uncategorized"
        lines.append(f"| #{tag} | {mapped_str} | {len(note_paths)} |")
    lines.append("")

    lines.append("## Reading + Contemplation + Synthesis/Critique Workflow")
    lines.append("")
    lines.append("### 1. Read")
    lines.append("- Start with notes in the skill categories that interest you most")
    lines.append("- Follow wikilinks between related notes")
    lines.append("")
    lines.append("### 2. Contemplate")
    lines.append("- Review tag clusters to identify theme concentrations")
    lines.append("- Compare notes across different skills for cross-pollination")
    lines.append("")
    lines.append("### 3. Synthesize")
    lines.append("- Merge notes from multiple skills into combined insights")
    lines.append("- Create new notes that bridge skill categories")
    lines.append("")
    lines.append("### 4. Critique")
    lines.append("- Check uncategorized notes for missing categorization")
    lines.append("- Verify sources and citations for research integrity")
    lines.append("- Identify gaps in the skill table coverage")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 social_science/skill_table.py Self-Test Suite")
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

    # Test 1: categorize_skill_by_content
    def test_categorize():
        text = "This note is about prose routing and writing pattern diagnosis for academic work."
        scores = categorize_skill_by_content(text)
        assert "humanizer" in scores
        assert scores["humanizer"] > 0
    check("categorize_skill_by_content matches humanizer", test_categorize)

    # Test 2: categorize_skill_by_content paperwork
    def test_categorize_paperwork():
        text = "This note covers citation management and bibliography formatting for papers."
        scores = categorize_skill_by_content(text)
        assert "paperwork" in scores
        assert scores["paperwork"] > 0
    check("categorize_skill_by_content matches paperwork", test_categorize_paperwork)

    # Test 3: scan_skill_table
    def test_scan_skill_table():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            write_file(os.path.join(tmp, "writing.md"),
                       "# Writing\n\n#ai\n\nProse routing and sectional chunking for academic integrity.")
            write_file(os.path.join(tmp, "papers.md"),
                       "# Papers\n\n#ml\n\nCitation management and bibliography formatting.")
            result = scan_skill_table(tmp, days=30)
            assert "humanizer" in result["skill_notes"]
            assert "paperwork" in result["skill_notes"]
            assert len(result["skill_notes"]["humanizer"]) >= 1
            assert len(result["skill_notes"]["paperwork"]) >= 1
        finally:
            shutil.rmtree(tmp)
    check("scan_skill_table categorizes notes into skills", test_scan_skill_table)

    # Test 4: generate_skill_table
    def test_generate_table():
        result = {
            "skill_notes": {
                "humanizer": [
                    {"path": "writing.md", "words": 100},
                ],
                "paperwork": [],
                "research-corpus": [],
                "superpower-socialscience": [],
                "academic-research": [],
                "open-science": [],
                "claude-academic": [],
            },
            "uncategorized": [
                {"path": "random.md", "words": 50, "tags": ["misc"]},
            ],
            "tag_skill_map": {
                "ai": ["writing.md"],
                "misc": ["random.md"],
            },
            "generated_at": "2026-01-01T00:00:00+00:00",
        }
        table = generate_skill_table(result)
        assert "# Coherent Table-of-Skills" in table
        assert "Humanizer" in table
        assert "Paperwork" in table
        assert "Uncategorized" in table
    check("generate_skill_table produces coherent table", test_generate_table)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Social Science — Skill Table (coherent skill catalog).",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    p_scan = sub.add_parser("scan", help="Scan vault notes and generate skill table (dry-run report)")
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

    print(f"📊 Building skill table (last {args.days} days)...\n")

    result = scan_skill_table(VAULT, days=args.days)
    report = generate_skill_table(result)
    print(report)

    if dry_run:
        print(f"\n📄 Run with --apply to write report to {SKILL_TABLE_DIR}/")
    else:
        os.makedirs(SKILL_TABLE_DIR, exist_ok=True)
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(SKILL_TABLE_DIR, f"skill-table-{date_str}.md")
        write_file(path, report)
        print(f"\n📄 Report written to {path}")


if __name__ == "__main__":
    main()
