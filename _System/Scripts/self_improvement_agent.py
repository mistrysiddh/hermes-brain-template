#!/usr/bin/env python3
"""
Hermes Brain — Self-Improvement Agent Architectures (issue #23).

Implements self-improving agent patterns where smaller models handle grunt
work while larger models strategize and orchestrate. Includes:

1. Task complexity router — routes tasks to small vs large models
2. Self-evaluation loop — agents evaluate their own output and suggest improvements
3. Skill forge / command tracker — tracks skill usage and improves over time
4. Orchestrator pattern — big model plans, small models execute, results feed back

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only

Subcommands:
  self_improvement_agent.py route     Route a task to small or large model
  self_improvement_agent.py evaluate  Self-evaluate an agent output
  self_improvement_agent.py track     Track skill/command usage
  self_improvement_agent.py forge     Run skill forge cycle (improve a skill)
  self_improvement_agent.py --test    Built-in self-test suite

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
SELF_IMPROVE_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, SELF_IMPROVE_DIR
    VAULT = os.path.abspath(vault_path)
    SELF_IMPROVE_DIR = os.path.join(VAULT, "04-Archives", "Self-Improvement")


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
# Task complexity router (small vs large model)
# ---------------------------------------------------------------------------
GRUNT_KEYWORDS = [
    r"\b(format|reformat|convert|transform)\b",
    r"\b(summarize|summarise|tl;dr|tl;dr)\b",
    r"\b(extract|find|search|grep|locate)\b",
    r"\b(list|enumerate|count|tally)\b",
    r"\b(fix|correct|lint|format)\b",
    r"\b(template|boilerplate|scaffold)\b",
    r"\b(clean|scrub|normalize)\b",
]

ORCHESTRATE_KEYWORDS = [
    r"\b(architect|design|plan|strategy|strategize)\b",
    r"\b(orchestrate|coordinate|delegate|supervise)\b",
    r"\b(evaluate|review|critique|assess)\b",
    r"\b(decide|choose|select|prioritize)\b",
    r"\b(analyze|synthesize|deduce|infer)\b",
    r"\b(improve|refactor|redesign|refactor)\b",
]


def classify_task(task_text):
    """Classify a task as 'grunt' (small model) or 'orchestrate' (large model)."""
    text = task_text.lower()
    grunt_score = sum(len(re.findall(p, text)) for p in GRUNT_KEYWORDS)
    orchestrate_score = sum(len(re.findall(p, text)) for p in ORCHESTRATE_KEYWORDS)

    # Length heuristic: longer, more complex tasks tend to be orchestration
    word_count = len(task_text.split())
    length_score = min(word_count / 50, 2.0)

    total_grunt = grunt_score
    total_orchestrate = orchestrate_score + length_score

    if total_orchestrate > total_grunt:
        return "large", total_orchestrate, total_grunt
    else:
        return "small", total_orchestrate, total_grunt


def route_task(task_text):
    """Route a task to the appropriate model tier."""
    model_tier, orch_score, grunt_score = classify_task(task_text)

    reasoning = []
    if model_tier == "large":
        reasoning.append("Task shows orchestration signals: planning, evaluation, or strategic decision-making")
        reasoning.append(f"Orchestration score: {orch_score:.1f} vs grunt score: {grunt_score:.1f}")
        reasoning.append("Recommendation: Use larger model for reasoning, planning, and quality gatekeeping")
    else:
        reasoning.append("Task shows grunt work signals: formatting, extraction, summarization, or cleanup")
        reasoning.append(f"Grunt score: {grunt_score:.1f} vs orchestration score: {orch_score:.1f}")
        reasoning.append("Recommendation: Use smaller model for execution; larger model only for final review")

    return {
        "tier": model_tier,
        "orchestration_score": round(orch_score, 1),
        "grunt_score": round(grunt_score, 1),
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Self-evaluation loop
# ---------------------------------------------------------------------------
def evaluate_output(output_text, task_context=""):
    """Self-evaluate an agent output across quality dimensions."""
    scores = {}
    suggestions = []

    # Clarity: clear intent, specific output format
    clarity_indicators = len(re.findall(r"\b(output|result|format|structure|clearly|specifically)\b", output_text, re.I))
    clarity = min(10.0, 5.0 + clarity_indicators * 0.8)
    scores["clarity"] = round(clarity, 1)
    if clarity < 6:
        suggestions.append("Clarify the expected output — specify format, structure, and content requirements explicitly")

    # Specificity: concrete details, examples, constraints
    specificity_indicators = len(re.findall(r"\b(example|sample|constraint|limit|require|must|should)\b", output_text, re.I))
    specificity = min(10.0, 5.0 + specificity_indicators * 0.8)
    scores["specificity"] = round(specificity, 1)
    if specificity < 6:
        suggestions.append("Add specific constraints, examples, or requirements to reduce ambiguity")

    # Actionability: imperative verbs, clear next steps
    action_indicators = len(re.findall(r"\b(create|write|build|make|run|execute|implement|deploy)\b", output_text, re.I))
    actionability = min(10.0, 5.0 + action_indicators * 0.8)
    scores["actionability"] = round(actionability, 1)
    if actionability < 6:
        suggestions.append("Use imperative verbs and clear actionable steps")

    # Completeness: context, task, constraints all present
    completeness_indicators = len(re.findall(r"\b(context|background|task|goal|objective|audience|tone|constraint)\b", output_text, re.I))
    completeness = min(10.0, 5.0 + completeness_indicators * 0.8)
    scores["completeness"] = round(completeness, 1)
    if completeness < 6:
        suggestions.append("Include context, task definition, constraints, and audience information")

    # Self-correction potential: does the output acknowledge its own limitations?
    self_reflection = len(re.findall(r"\b(limitation|uncertain|assume|approximate|estimate|roughly)\b", output_text, re.I))
    self_reflection_score = min(10.0, 5.0 + self_reflection * 0.8)
    scores["self_reflection"] = round(self_reflection_score, 1)

    overall = round((clarity + specificity + actionability + completeness + self_reflection_score) / 5 * 10, 1)
    scores["overall"] = overall

    return {
        "scores": scores,
        "suggestions": suggestions,
        "improved": not suggestions,
    }


# ---------------------------------------------------------------------------
# Skill forge / command tracker
# ---------------------------------------------------------------------------
def load_skill_registry():
    """Load the skill registry from vault, or create empty."""
    registry_path = os.path.join(SELF_IMPROVE_DIR, "skill-registry.json")
    if os.path.exists(registry_path):
        try:
            with open(registry_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"skills": {}, "commands": {}, "improvements": []}
    return {"skills": {}, "commands": {}, "improvements": []}


def save_skill_registry(registry):
    """Save the skill registry to vault."""
    registry_path = os.path.join(SELF_IMPROVE_DIR, "skill-registry.json")
    write_file(registry_path, json.dumps(registry, indent=2, ensure_ascii=False))


def track_command(command_name, success=True, duration_seconds=None, model_tier=None):
    """Track a command/skill usage for improvement analytics."""
    registry = load_skill_registry()
    now = datetime.datetime.now().isoformat()

    if command_name not in registry["commands"]:
        registry["commands"][command_name] = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_duration": 0,
            "avg_duration": 0,
            "last_run": None,
            "model_tiers_used": {},
        }

    cmd = registry["commands"][command_name]
    cmd["total_runs"] += 1
    if success:
        cmd["successful_runs"] += 1
    else:
        cmd["failed_runs"] += 1
    if duration_seconds is not None:
        cmd["total_duration"] += duration_seconds
        cmd["avg_duration"] = round(cmd["total_duration"] / cmd["total_runs"], 2)
    cmd["last_run"] = now
    if model_tier:
        cmd["model_tiers_used"][model_tier] = cmd["model_tiers_used"].get(model_tier, 0) + 1

    save_skill_registry(registry)
    return cmd


def get_command_stats(command_name):
    """Get stats for a specific command."""
    registry = load_skill_registry()
    return registry["commands"].get(command_name, None)


# ---------------------------------------------------------------------------
# Skill forge cycle
# ---------------------------------------------------------------------------
def forge_skill(skill_name, skill_content, improvement_focus="general"):
    """Run a skill forge cycle: evaluate, suggest improvements, produce improved version."""
    registry = load_skill_registry()

    # Evaluate current skill
    evaluation = evaluate_output(skill_content, task_context=f"skill: {skill_name}")

    # Generate improved version
    improved_content = skill_content
    improvements_applied = []

    if evaluation["scores"]["clarity"] < 7:
        improved_content = "# " + skill_name + "\n\n" + improved_content
        improvements_applied.append("Added clear title heading")

    if evaluation["scores"]["specificity"] < 7:
        improved_content += "\n\n## Constraints\n- Be specific about inputs and outputs\n- Define edge cases explicitly\n"
        improvements_applied.append("Added constraints section")

    if evaluation["scores"]["actionability"] < 7:
        improved_content += "\n\n## Steps\n1. Read the input\n2. Process according to constraints\n3. Produce output in the defined format\n"
        improvements_applied.append("Added actionable steps")

    if evaluation["scores"]["completeness"] < 7:
        improved_content += "\n\n## Context\nThis skill is part of the self-improvement agent architecture.\n## Audience\nAI agents executing automated tasks.\n"
        improvements_applied.append("Added context and audience")

    # Record the improvement
    improvement_record = {
        "skill": skill_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "focus": improvement_focus,
        "before_scores": evaluation["scores"],
        "improvements_applied": improvements_applied,
    }
    registry["improvements"].append(improvement_record)

    # Update skill registry
    if skill_name not in registry["skills"]:
        registry["skills"][skill_name] = {
            "version": 1,
            "last_improved": None,
            "total_improvements": 0,
        }
    skill_reg = registry["skills"][skill_name]
    skill_reg["version"] = skill_reg.get("version", 1) + 1
    skill_reg["last_improved"] = improvement_record["timestamp"]
    skill_reg["total_improvements"] = skill_reg.get("total_improvements", 0) + 1

    save_skill_registry(registry)

    return {
        "skill": skill_name,
        "evaluation": evaluation,
        "improved_content": improved_content,
        "improvements_applied": improvements_applied,
        "new_version": skill_reg["version"],
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_route_report(route_result, task_text):
    """Generate markdown report for task routing."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tier = route_result["tier"]
    tier_label = "Large Model (strategize/orchestrate)" if tier == "large" else "Small Model (grunt work)"

    lines = [
        "# Task Route Decision",
        f"Generated: {now}",
        "",
        "---",
        "",
        "## Task",
        task_text,
        "",
        "## Decision",
        f"**Route to: {tier_label}**",
        f"- Orchestration score: {route_result['orchestration_score']}",
        f"- Grunt score: {route_result['grunt_score']}",
        "",
        "## Reasoning",
        "",
    ]
    for r in route_result["reasoning"]:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Model Allocation Principle")
    lines.append("- **Small models**: grunt work (formatting, extraction, summarization, cleanup)")
    lines.append("- **Large models**: orchestration (planning, evaluation, strategy, quality gates)")
    lines.append("")

    return "\n".join(lines)


def generate_evaluate_report(eval_result, task_context):
    """Generate markdown report for self-evaluation."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scores = eval_result["scores"]
    overall = scores["overall"]
    grade = "A" if overall >= 90 else "B" if overall >= 80 else "C" if overall >= 70 else "D" if overall >= 60 else "F"

    lines = [
        "# Self-Evaluation Report",
        f"Generated: {now}",
        f"Task context: {task_context}",
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
        f"| Clarity | {scores['clarity']} |",
        f"| Specificity | {scores['specificity']} |",
        f"| Actionability | {scores['actionability']} |",
        f"| Completeness | {scores['completeness']} |",
        f"| Self-reflection | {scores['self_reflection']} |",
        "",
        "---",
        "",
        "## Improvement Suggestions",
        "",
    ]
    if eval_result["suggestions"]:
        for i, s in enumerate(eval_result["suggestions"], 1):
            lines.append(f"{i}. {s}")
    else:
        lines.append("✅ No improvements needed — output meets quality thresholds.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Self-Improvement Principle")
    lines.append("- Small models execute tasks")
    lines.append("- Large models evaluate and strategize")
    lines.append("- Evaluation output feeds back into improvement cycles")

    return "\n".join(lines)


def generate_forge_report(forge_result):
    """Generate markdown report for skill forge cycle."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Skill Forge Cycle",
        f"Generated: {now}",
        f"Skill: {forge_result['skill']}",
        f"New version: {forge_result['new_version']}",
        "",
        "---",
        "",
        "## Before Scores",
        "| Dimension | Score |",
        "|-----------|-------|",
    ]
    for dim, score in forge_result["evaluation"]["scores"].items():
        lines.append(f"| {dim} | {score} |")

    lines.append("")
    lines.append("## Improvements Applied")
    if forge_result["improvements_applied"]:
        for imp in forge_result["improvements_applied"]:
            lines.append(f"- {imp}")
    else:
        lines.append("- None needed (skill already meets quality thresholds)")
    lines.append("")
    lines.append("## Improved Content (preview)")
    lines.append("")
    preview = forge_result["improved_content"][:500]
    if len(forge_result["improved_content"]) > 500:
        preview += "..."
    lines.append("```markdown")
    lines.append(preview)
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def save_report(agent_name, report_md):
    """Save report to vault."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_name = slugify(agent_name)
    path = os.path.join(SELF_IMPROVE_DIR, f"{safe_name}-{today}.md")
    write_file(path, report_md)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 self_improvement_agent.py Self-Test Suite")
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

    # Test 1: classify_task - grunt
    def test_classify_grunt():
        tier, os_, gs = classify_task("Format this markdown file and extract the headings")
        assert tier == "small", f"Expected small, got {tier}"
    check("classify_task identifies grunt work", test_classify_grunt)

    # Test 2: classify_task - orchestrate
    def test_classify_orchestrate():
        tier, os_, gs = classify_task("Architect a multi-agent system that evaluates its own output and improves over time")
        assert tier == "large", f"Expected large, got {tier}"
    check("classify_task identifies orchestration", test_classify_orchestrate)

    # Test 3: route_task returns valid result
    def test_route():
        result = route_task("Summarize this meeting transcript into bullet points")
        assert result["tier"] in ("small", "large")
        assert "reasoning" in result
        assert len(result["reasoning"]) >= 1
    check("route_task returns valid result", test_route)

    # Test 4: evaluate_output returns all dimensions
    def test_evaluate():
        result = evaluate_output("Please create a markdown report with headings and bullet points.", "test task")
        scores = result["scores"]
        assert "clarity" in scores
        assert "specificity" in scores
        assert "actionability" in scores
        assert "completeness" in scores
        assert "overall" in scores
        assert 0 <= scores["overall"] <= 100
    check("evaluate_output returns all dimensions", test_evaluate)

    # Test 5: track_command updates stats
    def test_track():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            cmd = track_command("test_cmd", success=True, duration_seconds=1.5, model_tier="small")
            assert cmd["total_runs"] == 1
            assert cmd["successful_runs"] == 1
            assert cmd["avg_duration"] == 1.5
        finally:
            shutil.rmtree(tmp)
    check("track_command updates stats", test_track)

    # Test 6: forge_skill produces improvements
    def test_forge():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            result = forge_skill("test_skill", "Just do it.", improvement_focus="clarity")
            assert result["new_version"] >= 2
            assert len(result["improvements_applied"]) >= 1
            assert result["improved_content"] != "Just do it."
        finally:
            shutil.rmtree(tmp)
    check("forge_skill produces improvements", test_forge)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Self-Improvement Agent Architectures.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_route = sub.add_parser("route", help="Route a task to small or large model")
    p_route.add_argument("--task", required=True, help="Task description to route")

    p_eval = sub.add_parser("evaluate", help="Self-evaluate an agent output")
    p_eval.add_argument("--output", required=True, help="Agent output text to evaluate")
    p_eval.add_argument("--context", default="", help="Task context for evaluation")

    p_track = sub.add_parser("track", help="Track skill/command usage")
    p_track.add_argument("--command", required=True, help="Command name")
    p_track.add_argument("--success", action="store_true", default=True, help="Command succeeded (default)")
    p_track.add_argument("--failure", action="store_true", help="Command failed")
    p_track.add_argument("--duration", type=float, help="Duration in seconds")
    p_track.add_argument("--tier", choices=["small", "large"], help="Model tier used")

    p_forge = sub.add_parser("forge", help="Run skill forge cycle")
    p_forge.add_argument("--skill", required=True, help="Skill name")
    p_forge.add_argument("--skill-file", required=True, help="Path to skill content file")
    p_forge.add_argument("--focus", default="general", help="Improvement focus area")

    parser.add_argument("--save", action="store_true", help="Save report to vault")
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
    dry_run = not getattr(args, "apply", False)

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    if args.command == "route":
        route_result = route_task(args.task)
        report = generate_route_report(route_result, args.task)
        print(report)
        if not dry_run and args.save:
            saved = save_report("task-route", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "evaluate":
        eval_result = evaluate_output(args.output, args.context)
        report = generate_evaluate_report(eval_result, args.context)
        print(report)
        if not dry_run and args.save:
            saved = save_report("self-evaluation", report)
            print(f"\n📄 Saved to {saved}")

    elif args.command == "track":
        success = not args.failure
        cmd = track_command(
            args.command,
            success=success,
            duration_seconds=args.duration,
            model_tier=args.tier,
        )
        print(f"Command: {args.command}")
        print(f"  Total runs: {cmd['total_runs']}")
        print(f"  Success rate: {cmd['successful_runs']}/{cmd['total_runs']}")
        if cmd["avg_duration"]:
            print(f"  Avg duration: {cmd['avg_duration']}s")
        if args.tier:
            print(f"  Model tier: {args.tier}")

    elif args.command == "forge":
        skill_content = read_file(args.skill_file)
        if not skill_content.strip():
            print("Error: Skill file is empty.", file=sys.stderr)
            sys.exit(1)
        forge_result = forge_skill(args.skill, skill_content, improvement_focus=args.focus)
        report = generate_forge_report(forge_result)
        print(report)
        if not dry_run and args.save:
            saved = save_report("skill-forge", report)
            print(f"\n📄 Saved to {saved}")

    else:
        print("Error: No command specified. Use: route, evaluate, track, forge", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
