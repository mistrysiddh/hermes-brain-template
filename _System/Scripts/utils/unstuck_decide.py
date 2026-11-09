#!/usr/bin/env python3
"""
Hermes Brain — Unstuck + Decide Skill (roadblock antidote + decision workflow).

Two modes:
  - unstuck: Analyze a roadblock situation and suggest structured antidotes
  - decide: Run a structured decision workflow (2x2 matrix, pros/cons, scoring)

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  unstuck_decide.py unstuck    Analyze a roadblock → suggest antidotes
  unstuck_decide.py decide     Run a structured decision workflow
  unstuck_decide.py --test     Built-in self-test suite

Unstuck categories:
  - starting: Can't begin a task
  - stuck_middle: Started but stalled
  - overwhelmed: Too much to do, don't know where to focus
  - blocked: External dependency blocking progress
  - perfectionism: Can't finish because it's not "perfect"
  - unclear: Don't know what the next step is

Decide modes:
  - pros_cons: Simple pros/cons list with scoring
  - matrix_2x2: 2x2 impact vs effort matrix
  - weighted: Weighted criteria scoring

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import json
import os
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
UNSTUCK_DIR = None
DECISIONS_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, UNSTUCK_DIR, DECISIONS_DIR
    VAULT = os.path.abspath(vault_path)
    UNSTUCK_DIR = os.path.join(VAULT, "01-Projects", "Unstuck")
    DECISIONS_DIR = os.path.join(VAULT, "03-Resources", "Decisions")


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


# ---------------------------------------------------------------------------
# Unstuck mode
# ---------------------------------------------------------------------------
UNSTUCK_ANTIDOTES = {
    "starting": [
        "Break the task into the smallest possible first step (2-minute rule)",
        "Write a 'shitty first draft' — perfection comes later",
        "Set a 10-minute timer and commit to stopping after",
        "Define what 'done' looks like for this session only",
    ],
    "stuck_middle": [
        "Work on a different subtask for 15 minutes, then come back",
        "Explain the problem out loud (rubber duck debugging)",
        "Skip the hard part and do the easy parts first",
        "Change your environment — different desk, cafe, or background noise",
    ],
    "overwhelmed": [
        "List every task, then pick ONE to do next — hide the rest",
        "Use the 'rule of 3': pick 3 priorities for today, ignore everything else",
        "Delegate or defer anything that isn't urgent or important",
        "Break each task into sub-tasks under 30 minutes",
    ],
    "blocked": [
        "Identify exactly who/what is unblocking you and send a specific ask",
        "Work on a different task while waiting for the blocker",
        "Find a workaround — can you proceed with partial information?",
        "Escalate: set a deadline for the blocker response, then escalate",
    ],
    "perfectionism": [
        "Ship a 'good enough' version first, iterate later",
        "Set a time limit — when it expires, ship what you have",
        "Ask: 'Will this matter in 3 months?' if not, simplify",
        "Share an imperfect draft for feedback instead of polishing alone",
    ],
    "unclear": [
        "Write down the very next physical action — not the project, the action",
        "Ask: 'What would make this clear?' and do that first",
        "Create a mind map or rough outline to see the shape of the work",
        "Talk to someone who has done this before",
    ],
}


def unstuck_analyze(situation, category=None):
    """Analyze a roadblock and return suggested antidotes."""
    if category and category in UNSTUCK_ANTIDOTES:
        antidotes = UNSTUCK_ANTIDOTES[category]
        category_label = category
    else:
        # Try to auto-detect category from keywords
        situation_lower = situation.lower()
        detected = None
        for cat in UNSTUCK_ANTIDOTES:
            keywords = {
                "starting": ["start", "begin", "initiate", "kickoff", "first step"],
                "stuck_middle": ["stuck", "middle", "stalled", "halfway", "bogged"],
                "overwhelmed": ["overwhelmed", "too much", "everything", "all at once"],
                "blocked": ["blocked", "waiting", "dependency", "can't proceed", "stuck on"],
                "perfectionism": ["perfect", "perfection", "polish", "not ready", "good enough"],
                "unclear": ["unclear", "don't know", "confused", "unsure", "lost"],
            }
            if any(k in situation_lower for k in keywords.get(cat, [])):
                detected = cat
                break
        category_label = detected or "general"
        antidotes = UNSTUCK_ANTIDOTES.get(
            category_label,
            [
                "Take a 10-minute break and come back with fresh eyes",
                "Write down exactly what is blocking you in one sentence",
                "Work on the smallest possible piece of the problem",
                "Ask for help — someone may have solved this before",
            ],
        )

    return {
        "category": category_label,
        "situation": situation,
        "antidotes": antidotes,
    }


# ---------------------------------------------------------------------------
# Decide mode
# ---------------------------------------------------------------------------
def decide_pros_cons(options):
    """Simple pros/cons decision framework."""
    results = []
    for opt in options:
        pros = opt.get("pros", [])
        cons = opt.get("cons", [])
        score = len(pros) - len(cons)
        results.append({
            "name": opt["name"],
            "pros": pros,
            "cons": cons,
            "score": score,
        })
    results.sort(key=lambda r: -r["score"])
    return results


def decide_matrix_2x2(options):
    """2x2 impact vs effort matrix."""
    results = []
    for opt in options:
        impact = opt.get("impact", 5)  # 1-10
        effort = opt.get("effort", 5)  # 1-10
        if impact >= 5 and effort <= 5:
            quadrant = "Quick win — do now"
        elif impact >= 5 and effort > 5:
            quadrant = "Major project — plan carefully"
        elif impact < 5 and effort <= 5:
            quadrant = "Fill-in — do if time permits"
        else:
            quadrant = "Avoid — low value, high effort"
        results.append({
            "name": opt["name"],
            "impact": impact,
            "effort": effort,
            "quadrant": quadrant,
        })
    # Sort: quick wins first, then major projects, then fill-ins, then avoid
    quadrant_order = {"Quick win — do now": 0, "Major project — plan carefully": 1,
                      "Fill-in — do if time permits": 2, "Avoid — low value, high effort": 3}
    results.sort(key=lambda r: quadrant_order.get(r["quadrant"], 99))
    return results


def decide_weighted(options, criteria):
    """Weighted criteria scoring."""
    results = []
    for opt in options:
        scores = opt.get("scores", {})
        total = sum(scores.get(c, 0) * criteria.get(c, 1) for c in criteria)
        max_possible = sum(10 * criteria.get(c, 1) for c in criteria)
        pct = round(total / max_possible * 100, 1) if max_possible > 0 else 0
        results.append({
            "name": opt["name"],
            "total": total,
            "percentage": pct,
            "scores": scores,
        })
    results.sort(key=lambda r: -r["total"])
    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_unstuck_report(analysis):
    """Generate markdown report for unstuck analysis."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Unstuck Analysis",
        f"Generated: {now}",
        f"Category: {analysis['category']}",
        "",
        "---",
        "",
        "## Situation",
        analysis["situation"],
        "",
        "---",
        "",
        "## Suggested Antidotes",
        "",
    ]
    for i, antidote in enumerate(analysis["antidotes"], 1):
        lines.append(f"{i}. {antidote}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Next Step")
    lines.append("")
    lines.append("Pick ONE antidote and try it for 15 minutes. If it doesn't help, try another.")
    lines.append("")
    lines.append("Save this analysis: `unstuck_decide.py --vault <path> unstuck --save`")

    return "\n".join(lines)


def generate_decide_report(method, results, options=None, criteria=None):
    """Generate markdown report for decision workflow."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Decision Analysis — {method.replace('_', ' ').title()}",
        f"Generated: {now}",
        "",
        "---",
        "",
    ]

    if method == "pros_cons":
        lines.append("## Options Ranked by Net Score (pros − cons)")
        lines.append("")
        lines.append("| Option | Score | Pros | Cons |")
        lines.append("|--------|-------|------|------|")
        for r in results:
            lines.append(
                f"| {r['name']} | {r['score']} | {len(r['pros'])} | {len(r['cons'])} |"
            )
        lines.append("")
        lines.append("### Details")
        for r in results:
            lines.append(f"#### {r['name']}")
            if r["pros"]:
                lines.append("**Pros:**")
                for p in r["pros"]:
                    lines.append(f"- {p}")
            if r["cons"]:
                lines.append("**Cons:**")
                for c in r["cons"]:
                    lines.append(f"- {c}")
            lines.append("")
        lines.append(f"## Recommendation: **{results[0]['name']}**")
        lines.append("")

    elif method == "matrix_2x2":
        lines.append("## 2×2 Impact vs Effort Matrix")
        lines.append("")
        lines.append("| Option | Impact | Effort | Quadrant |")
        lines.append("|--------|--------|--------|----------|")
        for r in results:
            lines.append(
                f"| {r['name']} | {r['impact']} | {r['effort']} | {r['quadrant']} |"
            )
        lines.append("")
        quick_wins = [r for r in results if r["quadrant"] == "Quick win — do now"]
        if quick_wins:
            lines.append(f"## Recommendation: **{quick_wins[0]['name']}** (quick win)")
        else:
            lines.append(f"## Recommendation: **{results[0]['name']}**")
        lines.append("")

    elif method == "weighted":
        lines.append("## Weighted Criteria Scoring")
        lines.append("")
        lines.append("| Option | Total | % |")
        lines.append("|--------|-------|---|")
        for r in results:
            lines.append(f"| {r['name']} | {r['total']} | {r['percentage']}% |")
        lines.append("")
        lines.append(f"## Recommendation: **{results[0]['name']}**")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Save this decision: `unstuck_decide.py --vault <path> decide --save`")

    return "\n".join(lines)


def save_unstuck_to_vault(analysis):
    """Save unstuck analysis to vault."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_name = slugify(analysis["category"]) + "-" + today
    path = os.path.join(UNSTUCK_DIR, f"Unstuck-{safe_name}.md")
    content = generate_unstuck_report(analysis)
    write_file(path, content)
    return path


def save_decision_to_vault(method, results, options=None, criteria=None):
    """Save decision to vault."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(DECISIONS_DIR, f"Decision-{method}-{today}.md")
    content = generate_decide_report(method, results, options, criteria)
    write_file(path, content)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 unstuck_decide.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: unstuck_analyze with explicit category
    try:
        result = unstuck_analyze("I can't start writing this report", category="starting")
        assert result["category"] == "starting"
        assert len(result["antidotes"]) >= 1
        assert "2-minute rule" in result["antidotes"][0]
        print("✅ Test 1: unstuck_analyze with explicit category")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: unstuck_analyze auto-detects category
    try:
        result = unstuck_analyze("I'm overwhelmed with too many tasks")
        assert result["category"] == "overwhelmed"
        assert len(result["antidotes"]) >= 1
        print("✅ Test 2: unstuck_analyze auto-detects category")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: unstuck_analyze falls back to general
    try:
        result = unstuck_analyze("something completely random xyz")
        assert result["category"] == "general"
        assert len(result["antidotes"]) >= 1
        print("✅ Test 3: unstuck_analyze falls back to general")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: decide_pros_cons ranks correctly
    try:
        options = [
            {"name": "A", "pros": ["fast", "cheap"], "cons": ["risky"]},
            {"name": "B", "pros": ["safe"], "cons": ["slow", "expensive", "complex"]},
            {"name": "C", "pros": ["balanced", "reliable"], "cons": []},
        ]
        results = decide_pros_cons(options)
        assert results[0]["name"] == "C", f"Expected C first, got {results[0]['name']}"
        assert results[0]["score"] == 2
        assert results[1]["name"] == "A"
        assert results[1]["score"] == 1
        assert results[2]["name"] == "B"
        assert results[2]["score"] == -2
        print("✅ Test 4: decide_pros_cons ranks correctly")
        passed += 1
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1

    # Test 5: decide_matrix_2x2 categorizes correctly
    try:
        options = [
            {"name": "Quick win", "impact": 8, "effort": 2},
            {"name": "Big project", "impact": 9, "effort": 8},
            {"name": "Fill-in", "impact": 3, "effort": 3},
            {"name": "Avoid", "impact": 2, "effort": 9},
        ]
        results = decide_matrix_2x2(options)
        assert results[0]["quadrant"] == "Quick win — do now"
        assert results[1]["quadrant"] == "Major project — plan carefully"
        assert results[2]["quadrant"] == "Fill-in — do if time permits"
        assert results[3]["quadrant"] == "Avoid — low value, high effort"
        print("✅ Test 5: decide_matrix_2x2 categorizes correctly")
        passed += 1
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1

    # Test 6: decide_weighted scores correctly
    try:
        criteria = {"cost": 2, "speed": 1, "quality": 3}
        options = [
            {"name": "Option X", "scores": {"cost": 8, "speed": 5, "quality": 9}},
            {"name": "Option Y", "scores": {"cost": 4, "speed": 9, "quality": 6}},
        ]
        results = decide_weighted(options, criteria)
        # X: 8*2 + 5*1 + 9*3 = 16+5+27 = 48; max: 10*(2+1+3)=60; pct=80
        # Y: 4*2 + 9*1 + 6*3 = 8+9+18 = 35; pct=58.3
        assert results[0]["name"] == "Option X"
        assert results[0]["total"] == 48
        assert results[0]["percentage"] == 80.0
        assert results[1]["name"] == "Option Y"
        assert results[1]["total"] == 35
        print("✅ Test 6: decide_weighted scores correctly")
        passed += 1
    except Exception as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1

    # Test 7: generate_unstuck_report renders
    try:
        analysis = unstuck_analyze("I'm blocked waiting for API access", category="blocked")
        report = generate_unstuck_report(analysis)
        assert "# Unstuck Analysis" in report
        assert "blocked" in report.lower()
        assert len(analysis["antidotes"]) > 0
        print("✅ Test 7: generate_unstuck_report renders")
        passed += 1
    except Exception as e:
        print(f"❌ Test 7 failed: {e}")
        failed += 1

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Unstuck + Decide — roadblock antidote + decision workflow.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # unstuck subcommand
    p_unstuck = sub.add_parser("unstuck", help="Analyze a roadblock → suggest antidotes")
    p_unstuck.add_argument("--situation", required=True, help="Describe the roadblock situation")
    p_unstuck.add_argument("--category", help="Category: starting, stuck_middle, overwhelmed, blocked, perfectionism, unclear")
    p_unstuck.add_argument("--save", action="store_true", help="Save analysis to vault")

    # decide subcommand
    p_decide = sub.add_parser("decide", help="Run a structured decision workflow")
    p_decide.add_argument("--method", choices=["pros_cons", "matrix_2x2", "weighted"],
                          default="pros_cons", help="Decision method (default: pros_cons)")
    p_decide.add_argument("--options-file", help="JSON file with options data")
    p_decide.add_argument("--criteria-file", help="JSON file with weighted criteria (for weighted method)")
    p_decide.add_argument("--save", action="store_true", help="Save decision to vault")

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

    if args.command == "unstuck":
        analysis = unstuck_analyze(args.situation, category=args.category)
        report = generate_unstuck_report(analysis)
        print(report)
        if args.save:
            saved = save_unstuck_to_vault(analysis)
            print(f"\n📄 Saved to {saved}")
        return

    if args.command == "decide":
        if not args.options_file:
            print("Error: --options-file <path> is required for decide command.", file=sys.stderr)
            sys.exit(1)
        with open(args.options_file, encoding="utf-8") as f:
            options = json.load(f)

        criteria = {}
        if args.criteria_file:
            with open(args.criteria_file, encoding="utf-8") as f:
                criteria = json.load(f)

        if args.method == "pros_cons":
            results = decide_pros_cons(options)
        elif args.method == "matrix_2x2":
            results = decide_matrix_2x2(options)
        else:
            results = decide_weighted(options, criteria)

        report = generate_decide_report(args.method, results, options, criteria)
        print(report)
        if args.save:
            saved = save_decision_to_vault(args.method, results, options, criteria)
            print(f"\n📄 Saved to {saved}")
        return

    print("Error: No command specified. Use 'unstuck' or 'decide'.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
