#!/usr/bin/env python3
"""
Hermes Brain — Prompt Quality Checker (issue #22).

Analyzes prompts for quality preservation across models:
- Clarity: how clear is the intent and expected output
- Specificity: how specific are the requirements and constraints
- Actionability: can the prompt be acted on without clarification
- Structure: is the prompt well-organized with clear sections
- Completeness: are all necessary elements present (context, task, format)

Produces a quality score (0-100) and improvement suggestions.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  prompt_quality.py check     Check a single prompt's quality
  prompt_quality.py scan      Scan vault for prompts and score them
  prompt_quality.py --test    Built-in self-test suite

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
QUALITY_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, QUALITY_DIR
    VAULT = os.path.abspath(vault_path)
    QUALITY_DIR = os.path.join(VAULT, "04-Archives", "Metrics", "prompt-quality")


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
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower()).strip("-_")
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


# ---------------------------------------------------------------------------
# Prompt quality analysis
# ---------------------------------------------------------------------------
# Clarity indicators
CLARITY_POSITIVE = [
    r"\b(should|must|will|need to|required to)\b",
    r"\b(output|result|answer|response|return)\b",
    r"\b(format|structure|template|layout)\b",
    r"\b(step|stage|phase|first|then|finally)\b",
]
CLARITY_NEGATIVE = [
    r"\b(maybe|perhaps|possibly|might|could|maybe)\b",
    r"\b(something|anything|stuff|things)\b",
    r"\b(whatever|whenever|wherever)\b",
]

# Specificity indicators
SPECIFICITY_POSITIVE = [
    r"\b(exactly|precisely|specifically|particularly)\b",
    r"\b(length|words|characters|lines|pages)\b",
    r"\b(format|json|markdown|csv|yaml|xml)\b",
    r"\b(example|sample|template|instance)\b",
    r"\b(limit|maximum|minimum|at least|at most)\b",
]
SPECIFICITY_NEGATIVE = [
    r"\b(some|few|several|many|a lot)\b",
    r"\b(short|long|big|small|fast|slow)\b",
]

# Actionability indicators
ACTIONABILITY_POSITIVE = [
    r"\b(create|write|build|make|generate|produce)\b",
    r"\b(analyze|review|check|verify|validate)\b",
    r"\b(list|enumerate|identify|find|locate)\b",
    r"\b(compare|contrast|evaluate|assess)\b",
    r"\b(explain|describe|detail|outline|summarize)\b",
]
ACTIONABILITY_NEGATIVE = [
    r"\b(think about|consider|ponder|reflect)\b",
    r"\b(maybe try|perhaps look|possibly check)\b",
]

# Structure indicators
STRUCTURE_POSITIVE = [
    r"\n#{1,6}\s",  # headings
    r"\n[-*+]\s",  # bullet lists
    r"\n\d+\.\s",  # numbered lists
    r"\n\s*[-*+]\s",  # nested lists
    r"```",  # code blocks
    r"\|\s*.*\s*\|",  # tables
]
STRUCTURE_NEGATIVE = [
    r"\n\s*\n\s*\n\s*\n",  # too many blank lines
]

# Completeness indicators
COMPLETENESS_POSITIVE = [
    r"\b(context|background|overview|situation)\b",
    r"\b(task|goal|objective|purpose|aim)\b",
    r"\b(constraint|requirement|condition|rule)\b",
    r"\b(audience|user|reader|recipient)\b",
    r"\b(tone|style|voice|persona)\b",
]


def score_clarity(text):
    """Score clarity 0-10."""
    score = 5.0  # base
    for pattern in CLARITY_POSITIVE:
        matches = len(re.findall(pattern, text, re.I))
        score += min(matches * 0.5, 2.0)
    for pattern in CLARITY_NEGATIVE:
        matches = len(re.findall(pattern, text, re.I))
        score -= min(matches * 0.3, 1.5)
    return max(0.0, min(10.0, score))


def score_specificity(text):
    """Score specificity 0-10."""
    score = 5.0  # base
    for pattern in SPECIFICITY_POSITIVE:
        matches = len(re.findall(pattern, text, re.I))
        score += min(matches * 0.5, 2.0)
    for pattern in SPECIFICITY_NEGATIVE:
        matches = len(re.findall(pattern, text, re.I))
        score -= min(matches * 0.3, 1.5)
    return max(0.0, min(10.0, score))


def score_actionability(text):
    """Score actionability 0-10."""
    score = 5.0  # base
    for pattern in ACTIONABILITY_POSITIVE:
        matches = len(re.findall(pattern, text, re.I))
        score += min(matches * 0.5, 2.0)
    for pattern in ACTIONABILITY_NEGATIVE:
        matches = len(re.findall(pattern, text, re.I))
        score -= min(matches * 0.3, 1.5)
    # Bonus for clear imperative verbs at start of sentences
    imperative = len(re.findall(r"^\s*(create|write|build|make|analyze|review|list|explain)\b", text, re.M | re.I))
    score += min(imperative * 0.5, 2.0)
    return max(0.0, min(10.0, score))


def score_structure(text):
    """Score structure 0-10."""
    score = 5.0  # base
    for pattern in STRUCTURE_POSITIVE:
        matches = len(re.findall(pattern, text, re.I))
        score += min(matches * 0.4, 2.0)
    for pattern in STRUCTURE_NEGATIVE:
        matches = len(re.findall(pattern, text, re.I))
        score -= min(matches * 0.3, 1.0)
    # Bonus for having sections separated by blank lines + headings
    if re.search(r"\n#{1,6}\s", text) and len(text.split("\n\n")) > 3:
        score += 1.0
    return max(0.0, min(10.0, score))


def score_completeness(text):
    """Score completeness 0-10."""
    score = 5.0  # base
    for pattern in COMPLETENESS_POSITIVE:
        matches = len(re.findall(pattern, text, re.I))
        score += min(matches * 0.4, 2.0)
    # Penalty for very short prompts (likely missing context)
    word_count = len(text.split())
    if word_count < 10:
        score -= 3.0
    elif word_count < 25:
        score -= 1.5
    return max(0.0, min(10.0, score))


def analyze_prompt(text):
    """Analyze a prompt and return quality scores."""
    clarity = score_clarity(text)
    specificity = score_specificity(text)
    actionability = score_actionability(text)
    structure = score_structure(text)
    completeness = score_completeness(text)

    overall = round((clarity + specificity + actionability + structure + completeness) / 5 * 10, 1)

    # Generate suggestions
    suggestions = []
    if clarity < 6:
        suggestions.append("Clarify the expected output format and intent — use more directive language (should, must, will).")
    if specificity < 6:
        suggestions.append("Add specific constraints: length, format, examples, or limits.")
    if actionability < 6:
        suggestions.append("Use clear imperative verbs (create, write, analyze, list) at the start of instructions.")
    if structure < 6:
        suggestions.append("Add structure: headings, bullet lists, numbered steps, or code blocks.")
    if completeness < 6:
        suggestions.append("Include context, task definition, constraints, audience, and tone requirements.")

    if not suggestions:
        suggestions.append("Prompt is well-structured. Consider adding examples or edge cases for even better results.")

    return {
        "clarity": round(clarity, 1),
        "specificity": round(specificity, 1),
        "actionability": round(actionability, 1),
        "structure": round(structure, 1),
        "completeness": round(completeness, 1),
        "overall": overall,
        "suggestions": suggestions,
    }


def generate_check_report(prompt_text, analysis):
    """Generate markdown report for a single prompt check."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    overall = analysis["overall"]
    grade = "A" if overall >= 90 else "B" if overall >= 80 else "C" if overall >= 70 else "D" if overall >= 60 else "F"

    lines = [
        "# Prompt Quality Check",
        f"Generated: {now}",
        "",
        "---",
        "",
        "## Overall Score",
        f"**{overall}/100 — Grade {grade}**",
        "",
        "---",
        "",
        "## Dimension Scores",
        "| Dimension | Score (0-10) |",
        "|-----------|--------------|",
        f"| Clarity | {analysis['clarity']} |",
        f"| Specificity | {analysis['specificity']} |",
        f"| Actionability | {analysis['actionability']} |",
        f"| Structure | {analysis['structure']} |",
        f"| Completeness | {analysis['completeness']} |",
        "",
        "---",
        "",
        "## Improvement Suggestions",
        "",
    ]
    for i, s in enumerate(analysis["suggestions"], 1):
        lines.append(f"{i}. {s}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Prompt Preview")
    lines.append("")
    preview = prompt_text[:300]
    if len(prompt_text) > 300:
        preview += "..."
    lines.append(f"> {preview.replace(chr(10), chr(10) + '> ')}")
    lines.append("")

    return "\n".join(lines)


def generate_scan_report(results):
    """Generate markdown report for a vault scan."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(results)
    if total == 0:
        return "# Prompt Quality Scan\n\nNo prompts found in vault."

    avg_overall = round(sum(r["overall"] for r in results) / total, 1)
    avg_by_dim = {
        dim: round(sum(r[dim] for r in results) / total, 1)
        for dim in ("clarity", "specificity", "actionability", "structure", "completeness")
    }

    lines = [
        "# Prompt Quality Scan",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Prompts scanned**: {total}",
        f"- **Average overall score**: {avg_overall}/100",
        "",
        "### Average dimension scores",
        f"- Clarity: {avg_by_dim['clarity']}/10",
        f"- Specificity: {avg_by_dim['specificity']}/10",
        f"- Actionability: {avg_by_dim['actionability']}/10",
        f"- Structure: {avg_by_dim['structure']}/10",
        f"- Completeness: {avg_by_dim['completeness']}/10",
        "",
        "---",
        "",
        "## Results by Prompt",
        "| Prompt | Overall | Clarity | Specificity | Actionability | Structure | Completeness |",
        "|--------|---------|---------|-------------|---------------|-----------|--------------|",
    ]

    for r in sorted(results, key=lambda x: -x["overall"])[:30]:
        lines.append(
            f"| `{r['name']}` | {r['overall']} | {r['clarity']} | {r['specificity']} | "
            f"{r['actionability']} | {r['structure']} | {r['completeness']} |"
        )

    if total > 30:
        lines.append(f"| ... and {total - 30} more | | | | | | |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Lowest Scoring Prompts (needs improvement)")
    lines.append("")
    low = sorted(results, key=lambda x: x["overall"])[:10]
    for r in low:
        if r["overall"] < 70:
            lines.append(f"- **`{r['name']}`** — {r['overall']}/100")
            for s in r.get("suggestions", [])[:2]:
                lines.append(f"  - {s}")
        else:
            break

    return "\n".join(lines)


def find_prompts_in_vault():
    """Find potential prompts in vault notes."""
    prompts = []
    for full, rel, name, content in walk_md(VAULT):
        # Heuristic: notes that look like prompts (contain imperative verbs, task language)
        text = content.lower()
        prompt_indicators = [
            r"\b(please|can you|could you)\b",
            r"\b(write|create|analyze|review|explain|generate)\b",
            r"\b(instructions|prompt|task|instruction)\b",
        ]
        indicator_count = sum(len(re.findall(p, text)) for p in prompt_indicators)
        if indicator_count >= 2:
            prompts.append({
                "rel_path": rel,
                "name": name,
                "content": content,
            })
    return prompts


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 prompt_quality.py Self-Test Suite")
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

    # Test 1: score_clarity
    def test_clarity():
        high = "Please write a detailed analysis of the quarterly sales data. Output in markdown format with a table."
        low = "Do something with the data."
        assert score_clarity(high) > score_clarity(low), "High clarity should score higher"
    check("score_clarity distinguishes high/low", test_clarity)

    # Test 2: score_specificity
    def test_specificity():
        high = "Write exactly 500 words in JSON format with at least 3 examples."
        low = "Write something."
        assert score_specificity(high) > score_specificity(low), "High specificity should score higher"
    check("score_specificity distinguishes high/low", test_specificity)

    # Test 3: score_actionability
    def test_actionability():
        high = "Create a list of all users and verify their permissions."
        low = "Think about users."
        assert score_actionability(high) > score_actionability(low), "High actionability should score higher"
    check("score_actionability distinguishes high/low", test_actionability)

    # Test 4: score_structure
    def test_structure():
        high = "# Task\n\n- Step 1: Do this\n- Step 2: Do that\n\n```python\nprint('hello')\n```"
        low = "Just do it."
        assert score_structure(high) > score_structure(low), "High structure should score higher"
    check("score_structure distinguishes high/low", test_structure)

    # Test 5: score_completeness
    def test_completeness():
        high = "Context: We are building a dashboard. Task: Create a chart. Constraints: Use Python. Audience: Executives."
        low = "hi"
        assert score_completeness(high) > score_completeness(low), "High completeness should score higher"
    check("score_completeness distinguishes high/low", test_completeness)

    # Test 6: analyze_prompt returns all dimensions
    def test_analyze():
        result = analyze_prompt("Please write a Python script that analyzes CSV data and outputs a summary report in markdown format.")
        assert "clarity" in result
        assert "specificity" in result
        assert "actionability" in result
        assert "structure" in result
        assert "completeness" in result
        assert "overall" in result
        assert "suggestions" in result
        assert 0 <= result["overall"] <= 100
    check("analyze_prompt returns all dimensions", test_analyze)

    # Test 7: generate_check_report renders
    def test_report():
        analysis = analyze_prompt("Write a hello world script.")
        report = generate_check_report("Write a hello world script.", analysis)
        assert "# Prompt Quality Check" in report
        assert "Overall Score" in report
        assert "Improvement Suggestions" in report
    check("generate_check_report renders", test_report)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Prompt Quality Checker — analyze prompts for quality preservation.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_check = sub.add_parser("check", help="Check a single prompt's quality")
    p_check.add_argument("--prompt", help="Prompt text to analyze")
    p_check.add_argument("--prompt-file", help="Path to a file containing the prompt")
    p_check.add_argument("--save", action="store_true", help="Save report to vault")

    p_scan = sub.add_parser("scan", help="Scan vault for prompts and score them")
    p_scan.add_argument("--save", action="store_true", help="Save report to vault")

    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no file written (default)")
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
    dry_run = not getattr(args, "apply", False)

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    if args.command == "check":
        prompt_text = ""
        if args.prompt:
            prompt_text = args.prompt
        elif args.prompt_file:
            prompt_text = read_file(args.prompt_file)
        else:
            print("Error: --prompt or --prompt-file is required for check command.", file=sys.stderr)
            sys.exit(1)

        if not prompt_text.strip():
            print("Error: Prompt text is empty.", file=sys.stderr)
            sys.exit(1)

        analysis = analyze_prompt(prompt_text)
        report = generate_check_report(prompt_text, analysis)
        print(report)

        if not dry_run and args.save:
            saved = save_report("prompt-quality-check", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "scan":
        prompts = find_prompts_in_vault()
        results = []
        for p in prompts:
            analysis = analyze_prompt(p["content"])
            analysis["name"] = p["name"]
            analysis["rel_path"] = p["rel_path"]
            results.append(analysis)

        report = generate_scan_report(results)
        print(report)

        if not dry_run and args.save:
            saved = save_report("prompt-quality-scan", report)
            print(f"\n📄 Saved to {saved}")

    else:
        print("Error: No command specified. Use 'check' or 'scan'.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
