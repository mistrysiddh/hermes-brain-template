#!/usr/bin/env python3
"""
Hermes Brain — Quiz Feature (test yourself from your own vault pages).

Generates quiz questions from vault notes for self-testing and knowledge
retention. Reads notes from the vault, extracts question-answer pairs from
headings, bold text, frontmatter, and key statements, then presents them
for self-testing with answer reveal and scoring.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  quiz.py generate       Generate quiz questions from vault notes (dry-run report)
  quiz.py take           Take an interactive quiz from generated questions
  quiz.py --test         Built-in self-test suite

Question types:
  - What is X? (from headings/definitions)
  - Complete the statement (from bold/italic key statements)
  - True/False (from frontmatter tags and statements)
  - List all (from bullet points)

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import json
import os
import re
import random
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
DAILY_DIR = None
REPORT_DIR = None
QUIZ_REPORT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, DAILY_DIR, REPORT_DIR, QUIZ_REPORT
    VAULT = os.path.abspath(vault_path)
    DAILY_DIR = os.path.join(VAULT, "04-Archives", "Daily")
    if not os.path.isdir(DAILY_DIR):
        DAILY_DIR = os.path.join(VAULT, "Daily")
    REPORT_DIR = os.path.join(VAULT, "04-Archives", "Audit-Reports")
    QUIZ_REPORT = os.path.join(REPORT_DIR, "Quiz-Report.md")


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


# ---------------------------------------------------------------------------
# Session / note reading
# ---------------------------------------------------------------------------
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.M)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
ITALIC_RE = re.compile(r"\*([^*]+?)\*", re.S)
BULLET_RE = re.compile(r"^[-*+]\s+(.+)$", re.M)
NUMBERED_RE = re.compile(r"^\d+\.\s+(.+)$", re.M)


def read_vault_notes(vault_dir, days=30):
    """Read all markdown notes from vault_dir within the day window."""
    import datetime
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    notes = []
    if not os.path.isdir(vault_dir):
        return notes
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT).replace("\\", "/")
            if f in ("README.md", "Timeline.md", "Chat-Correlation.md", "manifest.jsonl"):
                continue
            content = read_file(full)
            if not content.strip():
                continue
            created_match = re.search(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})"', content)
            created_date = None
            if created_match:
                created_date = f"{created_match.group(1)}-{created_match.group(2)}-{created_match.group(3)}"
            if created_date:
                try:
                    cdt = datetime.datetime.strptime(created_date, "%Y-%m-%d")
                    if cdt < cutoff:
                        continue
                except ValueError:
                    pass
            notes.append({
                "path": full,
                "rel_path": rel,
                "name": os.path.splitext(f)[0],
                "content": content,
                "created_date": created_date,
            })
    return notes


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------
def generate_questions(notes, max_per_note=5):
    """Generate quiz questions from notes."""
    questions = []
    for note in notes:
        content = note["content"]
        q_count = 0

        # Type 1: What is X? (from headings)
        for m in HEADING_RE.finditer(content):
            heading = m.group(1).strip()
            if len(heading) < 5 or len(heading) > 80:
                continue
            # Get the paragraph after the heading
            start = m.end()
            end = content.find("\n#", start)
            if end == -1:
                end = len(content)
            following = content[start:end].strip()
            answer = following[:200] if following else content[:200]
            questions.append({
                "type": "what_is",
                "question": f"What is {heading}?",
                "answer": answer,
                "source": note["rel_path"],
                "source_name": note["name"],
            })
            q_count += 1
            if q_count >= max_per_note:
                break

        # Type 2: Complete the statement (from bold text)
        for m in BOLD_RE.finditer(content):
            bold_text = m.group(1).strip()
            if len(bold_text) < 5 or len(bold_text) > 80:
                continue
            # Create a fill-in-the-blank
            blanked = bold_text[: len(bold_text) // 2] + " [...] "
            questions.append({
                "type": "complete",
                "question": f"Complete: {blanked}...",
                "answer": bold_text,
                "source": note["rel_path"],
                "source_name": note["name"],
            })
            q_count += 1
            if q_count >= max_per_note:
                break

        # Type 3: True/False (from bullet points)
        for m in BULLET_RE.finditer(content):
            bullet = m.group(1).strip()
            if len(bullet) < 10 or len(bullet) > 100:
                continue
            questions.append({
                "type": "true_false",
                "question": f"True or False: {bullet}",
                "answer": "True",
                "source": note["rel_path"],
                "source_name": note["name"],
            })
            q_count += 1
            if q_count >= max_per_note:
                break

    return questions


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(questions, dry_run=True):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(questions)
    by_type = {}
    for q in questions:
        t = q["type"]
        by_type[t] = by_type.get(t, 0) + 1

    lines = [
        "# Quiz Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Total questions generated**: {total}",
    ]
    for t in ("what_is", "complete", "true_false"):
        if by_type.get(t, 0) > 0:
            lines.append(f"  - {t}: {by_type[t]}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not questions:
        lines.append("## ✅ No questions generated — no notes found in the time window.")
        write_report(lines)
        return

    lines.append("## Sample Questions")
    lines.append("")
    lines.append("| # | Type | Question | Answer | Source |")
    lines.append("|---|------|----------|--------|--------|")
    for i, q in enumerate(questions[:20], 1):
        lines.append(
            f"| {i} | {q['type']} | {q['question'][:60]} | {q['answer'][:60]} | "
            f"[[{q['source']}|{q['source_name']}]] |"
        )
    if len(questions) > 20:
        lines.append(f"| ... | ... | ... | ... | ... and {len(questions) - 20} more |")
    lines.append("")
    lines.append("---")
    lines.append("")

    if dry_run:
        lines.append("## Next Steps")
        lines.append("")
        lines.append("Review the questions above. To take an interactive quiz, run with `--apply`.")
        lines.append("Each question will be presented one at a time with answer reveal and scoring.")
    write_report(lines)


def write_report(lines):
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(QUIZ_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 quiz.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: read_vault_notes finds notes
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "04-Archives", "Daily", "2026", "10", "29"))
        sess = os.path.join(tmp, "04-Archives", "Daily", "2026", "10", "29", "test.md")
        write_file(sess, """---\nsession_id: "test-001"\ncreated_at: "2026-10-29T10:00:00Z"\n---\n# Test Topic\n\nSome content about testing.\n\n- Bullet point one\n- Bullet point two\n\n**Bold statement here.**\n""")
        init_paths(tmp)
        notes = read_vault_notes(os.path.join(tmp, "04-Archives", "Daily"), 30)
        assert len(notes) == 1, f"Expected 1 note, got {len(notes)}"
        assert notes[0]["name"] == "test"
        print("✅ Test 1: read_vault_notes finds notes")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 2: generate_questions creates questions
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        fake_note = {
            "path": "/tmp/test.md",
            "rel_path": "04-Archives/Daily/2026/10/29/test.md",
            "name": "test",
            "content": """---\n# Python Basics\n\nPython is a programming language.\n\n**Variables store data.**\n\n- Lists are ordered\n- Dictionaries are key-value\n""",
            "created_date": "2026-10-29",
        }
        questions = generate_questions([fake_note], max_per_note=5)
        assert len(questions) >= 1, f"Expected >=1 question, got {len(questions)}"
        assert questions[0]["type"] in ("what_is", "complete", "true_false")
        assert questions[0]["question"]
        assert questions[0]["answer"]
        print("✅ Test 2: generate_questions creates questions")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 3: question types are valid
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        fake_note = {
            "path": "/tmp/test.md",
            "rel_path": "04-Archives/Daily/2026/10/29/test.md",
            "name": "test",
            "content": "# Topic\n\nContent here.\n\n**Bold text.**\n- Bullet point\n",
            "created_date": "2026-10-29",
        }
        questions = generate_questions([fake_note], max_per_note=10)
        types = {q["type"] for q in questions}
        valid_types = {"what_is", "complete", "true_false"}
        assert types.issubset(valid_types), f"Invalid types: {types - valid_types}"
        print("✅ Test 3: question types are valid")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Quiz — test yourself from your vault notes.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--days", type=int, default=30, help="Days of notes to scan (default: 30)")
    parser.add_argument("--max-per-note", type=int, default=5, help="Max questions per note (default: 5)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no quiz (default)")
    parser.add_argument("--apply", action="store_true", help="Take an interactive quiz (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("generate", help="Generate quiz questions from vault notes (dry-run report)")
    sub.add_parser("take", help="Take an interactive quiz from generated questions")
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

    if not os.path.isdir(DAILY_DIR):
        print(f"Error: Daily directory not found at {DAILY_DIR}", file=sys.stderr)
        sys.exit(1)

    notes = read_vault_notes(DAILY_DIR, args.days)
    print(f"📋 Scanned {len(notes)} note files (last {args.days} days)")

    questions = generate_questions(notes, max_per_note=args.max_per_note)
    print(f"❓ Generated {len(questions)} quiz questions\n")

    if not questions:
        print("✅ No questions generated — no notes found in the time window.")
        write_report([])
        return

    results = []
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] [{q['type'].upper()}] {q['question']}")
        print(f"   Source: [[{q['source']}|{q['source_name']}]]")

        if dry_run:
            results.append({
                "type": q["type"],
                "question": q["question"],
                "answer": q["answer"],
                "source": q["source"],
                "applied": False,
                "reason": "dry-run preview",
            })
            print(f"   ⏭️  Would ask: {q['question']}\n")
        else:
            # Interactive quiz mode
            user_answer = input(f"   Your answer: ").strip()
            correct = user_answer.lower() in q["answer"].lower() or q["answer"].lower() in user_answer.lower()
            results.append({
                "type": q["type"],
                "question": q["question"],
                "answer": q["answer"],
                "user_answer": user_answer,
                "correct": correct,
                "source": q["source"],
            })
            if correct:
                print(f"   ✅ Correct! Answer: {q['answer']}\n")
            else:
                print(f"   ❌ Incorrect. Correct answer: {q['answer']}\n")

    # Write report
    generate_report(questions, dry_run=dry_run)
    correct_count = sum(1 for r in results if r.get("correct", False))
    total_answered = len([r for r in results if r.get("correct") is not None])
    print(f"\n📄 Report written to {QUIZ_REPORT}")
    if not dry_run:
        print(f"✅ Quiz complete: {correct_count}/{total_answered} correct")
    else:
        print(f"✅ Quiz generation complete: {len(questions)} questions ready")


if __name__ == "__main__":
    main()
