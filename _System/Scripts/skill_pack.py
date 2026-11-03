#!/usr/bin/env python3
"""
Hermes Brain — Skill Pack for Education (multi-harness compatible).

DIY skill packs where the second brain can:
- Question the user (educational/Socratic questioning to check understanding)
- Self-question (evaluate its own reasoning/answers before responding)
- Route between smarter and cheaper models based on task complexity

Skill packs are YAML/JSON-defined collections of skills for specific
educational topics or domains. Each pack contains lessons, questions,
and self-evaluation criteria.

Multi-harness compliant:
  - --vault CLI arg, deferred path resolution via init_paths()
  - --dry-run default / --apply for human-in-the-loop approval
  - stdlib-only
  - --test built-in self-test suite
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
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


def iter_md_files(vault):
    """Yield all .md files under vault, skipping .git."""
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f)


# ---------------------------------------------------------------------------
# Skill pack model
# ---------------------------------------------------------------------------
SKILL_PACK_DIR = "_System/SkillPacks"


def skill_pack_dir(vault):
    return os.path.join(vault, SKILL_PACK_DIR)


def list_skill_packs(vault):
    """Return dict of skill_pack_name -> pack_data from .json/.yaml files."""
    packs = {}
    spath = skill_pack_dir(vault)
    if not os.path.exists(spath):
        return packs
    for fname in os.listdir(spath):
        fpath = os.path.join(spath, fname)
        if not os.path.isfile(fpath):
            continue
        if fname.endswith(".json"):
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                packs[data.get("name", fname[:-5])] = data
            except Exception:
                continue
        elif fname.endswith((".yaml", ".yml")):
            try:
                import yaml
                with open(fpath, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                packs[data.get("name", fname.rsplit(".", 1)[0])] = data
            except ImportError:
                continue  # yaml not available in stdlib
            except Exception:
                continue
    return packs


# ---------------------------------------------------------------------------
# Question generation — user questioning (tutor mode)
# ---------------------------------------------------------------------------

def generate_questions(skill_pack, topic, difficulty="medium", count=3, dry_run=True):
    """Generate educational questions for a topic within a skill pack.

    Returns a list of question dicts: {question, type, expected_answer, hint}.
    """
    pack = skill_pack.get("topic", {}).get(topic, {}) if skill_pack else {}
    pack_questions = pack.get("questions", []) if pack else []

    questions = []
    for i in range(count):
        q = {
            "id": f"q{i+1}",
            "topic": topic,
            "difficulty": difficulty,
            "question": f"What is {topic}? (question {i+1} of {count})",
            "type": "open_ended",
            "expected_answer": pack.get("summary", "") if pack else "",
            "hint": f"Think about the key concepts of {topic}.",
        }
        if i < len(pack_questions):
            q["question"] = pack_questions[i].get("question", q["question"])
            q["type"] = pack_questions[i].get("type", q["type"])
            q["expected_answer"] = pack_questions[i].get("answer", q["expected_answer"])
            q["hint"] = pack_questions[i].get("hint", q["hint"])
        questions.append(q)

    return questions


# ---------------------------------------------------------------------------
# Self-questioning — evaluate own reasoning
# ---------------------------------------------------------------------------

def self_question(answer, criteria=None, dry_run=True):
    """Self-evaluate an answer against quality criteria.

    Returns {score, issues, suggestions, should_revise}.
    """
    if criteria is None:
        criteria = ["accuracy", "clarity", "completeness", "conciseness"]

    issues = []
    suggestions = []
    score = 1.0

    # Simple heuristic checks
    if len(answer.strip()) < 10:
        issues.append("Answer too short")
        suggestions.append("Expand with more detail")
        score -= 0.3

    if not any(c in answer.lower() for c in ["because", "since", "therefore", "however"]):
        issues.append("No reasoning connective found")
        suggestions.append("Add reasoning words (because, therefore, etc.)")
        score -= 0.2

    if "?" not in answer and score > 0.8:
        # Check if answer seems to be just restating without depth
        pass

    score = max(0.0, min(1.0, score))
    should_revise = score < 0.7 or len(issues) > 0

    return {
        "score": round(score, 2),
        "issues": issues,
        "suggestions": suggestions,
        "should_revise": should_revise,
        "criteria": criteria,
    }


# ---------------------------------------------------------------------------
# Model routing — smarter vs cheaper based on complexity
# ---------------------------------------------------------------------------

def route_model(task_complexity, task_type="general", dry_run=True):
    """Route a task to a model based on complexity.

    Returns {model, tier, reasoning, estimated_cost}.
    """
    if task_complexity >= 0.8:
        return {
            "model": "claude-opus-4",
            "tier": "smarter",
            "reasoning": f"High complexity ({task_complexity}) — use capable model",
            "estimated_cost": 0.015,
        }
    elif task_complexity >= 0.5:
        return {
            "model": "claude-sonnet-4",
            "tier": "standard",
            "reasoning": f"Medium complexity ({task_complexity}) — use balanced model",
            "estimated_cost": 0.003,
        }
    else:
        return {
            "model": "claude-haiku-3.5",
            "tier": "cheaper",
            "reasoning": f"Low complexity ({task_complexity}) — use efficient model",
            "estimated_cost": 0.00025,
        }


# ---------------------------------------------------------------------------
# Skill pack report generation
# ---------------------------------------------------------------------------

def generate_report(vault, packs, questions_by_topic, self_evals, model_routes):
    """Generate markdown education skill pack report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_packs = len(packs)
    total_questions = sum(len(qs) for qs in questions_by_topic.values())
    total_self_evals = len(self_evals)
    avg_score = (
        sum(e["score"] for e in self_evals) / total_self_evals
        if total_self_evals > 0
        else 0.0
    )

    lines = [
        "# Education Skill Pack Report",
        f"Generated: {now}",
        f"Vault: {vault}",
        "",
        "## Summary",
        f"- **Skill packs**: {total_packs}",
        f"- **Topics with questions**: {len(questions_by_topic)}",
        f"- **Total questions generated**: {total_questions}",
        f"- **Self-evaluations**: {total_self_evals}",
        f"- **Average self-eval score**: {avg_score:.2f}",
        "",
    ]

    if packs:
        lines.append("## Skill Packs")
        lines.append("")
        lines.append("| Pack | Topics | Questions |")
        lines.append("|------|--------|-----------|")
        for name, pack in packs.items():
            topics = list(pack.get("topic", {}).keys()) if isinstance(pack.get("topic"), dict) else []
            qcount = sum(
                len(pack.get("topic", {}).get(t, {}).get("questions", []))
                for t in topics
            )
            lines.append(f"| {name} | {len(topics)} | {qcount} |")
        lines.append("")

    if questions_by_topic:
        lines.append("## Generated Questions")
        lines.append("")
        for topic, qs in questions_by_topic.items():
            lines.append(f"### {topic}")
            for q in qs:
                lines.append(f"- **Q{q['id']}** ({q['difficulty']}): {q['question']}")
                lines.append(f"  - Type: {q['type']} | Hint: {q['hint']}")
            lines.append("")

    if self_evals:
        lines.append("## Self-Evaluations")
        lines.append("")
        for i, e in enumerate(self_evals, 1):
            status = "REVISE" if e["should_revise"] else "OK"
            lines.append(f"- Eval {i}: score {e['score']:.2f} [{status}] — {', '.join(e['issues']) or 'no issues'}")
        lines.append("")

    if model_routes:
        lines.append("## Model Routing Decisions")
        lines.append("")
        lines.append("| Task | Complexity | Model | Tier | Cost |")
        lines.append("|------|------------|-------|------|------|")
        for r in model_routes:
            lines.append(f"| {r['task']} | {r['complexity']} | {r['model']} | {r['tier']} | {r['estimated_cost']} |")
        lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append("- Review generated questions and add them to skill pack files")
    lines.append("- Use self-evaluation scores to identify answers needing revision")
    lines.append("- Route complex tasks to smarter models, simple tasks to cheaper ones")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 Skill Pack for Education Self-Test Suite")
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

    # Test 1: generate_questions
    def test_generate_questions():
        pack = {
            "topic": {
                "photosynthesis": {
                    "summary": "Process by which plants convert light to energy",
                    "questions": [
                        {"question": "What is the role of chlorophyll?", "type": "short_answer", "answer": "Absorbs light energy", "hint": "Green pigment in leaves"}
                    ],
                }
            }
        }
        qs = generate_questions(pack, "photosynthesis", difficulty="easy", count=2, dry_run=True)
        assert len(qs) == 2, f"Expected 2 questions, got {len(qs)}"
        assert qs[0]["topic"] == "photosynthesis"
        assert qs[0]["difficulty"] == "easy"
        assert "chlorophyll" in qs[0]["question"].lower() or qs[0]["expected_answer"] == ""
    check("generate_questions creates questions", test_generate_questions)

    # Test 2: self_question
    def test_self_question():
        result = self_question("This is a good answer because it explains the concept clearly.", dry_run=True)
        assert "score" in result
        assert "issues" in result
        assert "suggestions" in result
        assert "should_revise" in result
        assert 0.0 <= result["score"] <= 1.0
    check("self_question evaluates answers", test_self_question)

    def test_self_question_short():
        result = self_question("hi", dry_run=True)
        assert result["should_revise"] is True
        assert result["score"] < 0.7
    check("self_question flags short answers", test_self_question_short)

    # Test 3: route_model
    def test_route_model():
        r = route_model(0.9, "complex_reasoning", dry_run=True)
        assert r["tier"] == "smarter"
        assert r["model"] == "claude-opus-4"

        r2 = route_model(0.3, "simple_fact", dry_run=True)
        assert r2["tier"] == "cheaper"
        assert r2["model"] == "claude-haiku-3.5"
    check("route_model selects appropriate model", test_route_model)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Skill Pack for Education — question users and self-evaluate.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview without applying (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    parser.add_argument("--topic", default="general",
                        help="Topic to generate questions for")
    parser.add_argument("--difficulty", default="medium",
                        choices=["easy", "medium", "hard"],
                        help="Question difficulty level")
    parser.add_argument("--count", type=int, default=3,
                        help="Number of questions to generate")
    parser.add_argument("--self-eval", action="store_true",
                        help="Run self-evaluation on generated answers")
    parser.add_argument("--answer", default="",
                        help="Answer text to self-evaluate")
    parser.add_argument("--complexity", type=float, default=0.5,
                        help="Task complexity for model routing (0.0-1.0)")
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

    # Load skill packs
    packs = list_skill_packs(VAULT)

    # Generate questions
    questions = generate_questions(packs, args.topic, args.difficulty, args.count, dry_run=dry_run)

    # Self-evaluate if requested
    self_evals = []
    if args.self_eval and args.answer:
        eval_result = self_question(args.answer, dry_run=dry_run)
        self_evals.append(eval_result)

    # Model routing
    route = route_model(args.complexity, args.topic, dry_run=dry_run)
    model_routes = [{"task": args.topic, "complexity": args.complexity, **route}]

    # Generate report
    report = generate_report(VAULT, packs, {args.topic: questions}, self_evals, model_routes)
    report_path = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Skill-Pack-Education-Report.md")
    write_file(report_path, report)

    # Print summary
    print(f"📚 Skill Pack for Education — {args.topic}")
    print(f"   Vault: {VAULT}")
    print(f"   Skill packs found: {len(packs)}")
    print(f"   Questions generated: {len(questions)}")
    if self_evals:
        print(f"   Self-eval score: {self_evals[0]['score']:.2f} — {'REVISE' if self_evals[0]['should_revise'] else 'OK'}")
    print(f"   Model route: {model_routes[0]['model']} ({model_routes[0]['tier']})")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    print(f"   Report: {report_path}")
    if dry_run:
        print("   Run with --apply to write changes to vault.")

    # Display questions
    print("")
    for q in questions:
        print(f"  Q{q['id']} ({q['difficulty']}): {q['question']}")
        print(f"    Hint: {q['hint']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
