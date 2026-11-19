#!/usr/bin/env python3
"""
Hermes Brain — ADHD Execution Coach (Table 2: Coach execution in the moment).

Skills that spot a barrier — can't start, can't stop, overwhelmed, stuck
choosing — and steer you toward one small action. Based on the Table 2
feature comparison in the ADHD design draft (nd-skills, dsh-adhd-copilot,
adhd-copilot, openclaw-adhd-skills).

Subcommands:
  adhd-coach initiate      Can't start — concrete first action + activation bridges
  adhd-coach minimums      Reduce scope — functional minimums, defer polish
  adhd-coach decompose     Break big/ambiguous tasks into observable units
  adhd-coach time-estimate Time blindness — three-point ranges (best/realistic/worst)
  adhd-coach choices       Indecision — top 3 options, rest held back
  adhd-coach setshift      Repeating a failed approach — new strategy after 3 attempts
  adhd-coach closure       Jumping to new work — surface items >50% complete
  adhd-coach reanchor      Losing the thread — working-memory re-anchor
  adhd-coach inhibit       Check actions against goal before significant changes
  adhd-coach scaffold      Redesign environment after repeated failure
  adhd-coach velocity      Capture:ship ratio — healthy ~3:1, warn at ≥5:1
  adhd-coach --test        Built-in self-test suite

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Stdlib-only
  - --dry-run default, --apply for human-in-the-loop approval
  - --test self-tests

Exit code: 0 always (reporting tool, not a gate).
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
REPORT_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, REPORT_DIR
    VAULT = os.path.abspath(vault_path)
    REPORT_DIR = os.path.join(VAULT, "04-Archives", "Audit-Reports")


# ---------------------------------------------------------------------------
# Table 2 feature reference — mapped to this skill's subcommands
# ---------------------------------------------------------------------------
FEATURE_MAP = {
    "initiate": "Can't start — concrete first action + activation bridges",
    "minimums": "Reduce scope — preserve safety/function, defer polish",
    "decompose": "Big/ambiguous tasks — observable definition of done per unit",
    "time-estimate": "Time blindness — three-point ranges + stop rules",
    "choices": "Indecision — top 3 options only, rest hidden",
    "setshift": "Repeating a failed approach — genuinely different strategy after 3 attempts",
    "closure": "Jumping to new work — surface items >50% complete first",
    "reanchor": "Losing the thread — proactive working-memory re-anchor",
    "inhibit": "Check target and negative constraints before significant actions",
    "scaffold": "Redesign environment after repeated failure at point of action",
    "velocity": "Capture:ship ratio — ~3:1 healthy, ≥5:1 warns of decision paralysis",
}


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------
def self_test():
    """Built-in self-test suite. All must pass."""
    failures = []

    # Feature map covers all subcommands
    expected = {
        "initiate", "minimums", "decompose", "time-estimate", "choices",
        "setshift", "closure", "reanchor", "inhibit", "scaffold", "velocity",
    }
    missing = expected - set(FEATURE_MAP.keys())
    if missing:
        failures.append(f"Feature map missing: {missing}")

    # Each feature has a non-empty description
    for cmd, desc in FEATURE_MAP.items():
        if not desc or len(desc) < 10:
            failures.append(f"Feature {cmd}: description too short")

    if failures:
        print("SELF-TEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("SELF-TEST PASSED: all 11 subcommands mapped to Table 2 features")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def today_str():
    return datetime.date.today().isoformat()


def task_file_path():
    """Path to today's task file in the vault."""
    return os.path.join(VAULT, "01-Projects", f"adhd-tasks-{today_str()}.md")


def ensure_dirs():
    os.makedirs(os.path.join(VAULT, "01-Projects"), exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)


def write_report(name, content):
    ensure_dirs()
    path = os.path.join(REPORT_DIR, f"adhd-coach-{name}-{today_str()}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# Subcommand: initiate — can't start
# ---------------------------------------------------------------------------
def cmd_initiate(args):
    """Can't start — concrete first action + activation bridges.

    Table 2 features:
    - 2-minute launch with absurdly small first step
    - Never says "you just need to start"
    - If task is vague, first define what done looks like
    - Complex projects: step checklist with 5–25-minute steps
    - Five truthful activation bridges (interest, novelty, challenge,
      immediate feedback, body-doubling) — bans invented urgency/shame
    """
    task_name = args.task or input("What task are you trying to start? ")
    done_definition = args.done or input("What does 'done' look like? ")

    activation_bridges = [
        "Interest — what about this task is interesting or novel?",
        "Challenge — can you make it slightly harder/more engaging?",
        "Immediate feedback — how will you know you made progress?",
        "Body-doubling — can someone be present while you start?",
        "Novelty — is there a new angle or tool to try?",
    ]

    lines = [
        f"# ADHD Coach — Initiation: {task_name}",
        f"Date: {today_str()}",
        "",
        "## What done looks like",
        done_definition,
        "",
        "## First step (under 2 minutes)",
        "- [ ] Define the absurdly small first action (under 2 minutes)",
        "",
        "## Activation bridges (pick one)",
    ]
    for bridge in activation_bridges:
        lines.append(f"- [ ] {bridge}")
    lines += [
        "",
        "## Banned phrases",
        "- 'You just need to start'",
        "- Invented urgency or fake deadlines",
        "- Shame-based language",
        "",
        "## If the task is vague",
        "- First define what done looks like (done above)",
        "- Then break into 5–25-minute steps with check-in invitations",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("initiate", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: minimums — reduce scope
# ---------------------------------------------------------------------------
def cmd_minimums(args):
    """Reduce scope — functional minimums, defer polish.

    Table 2 features:
    - Preserve safety and function, defer polish
    - Execute the reduced version when allowed
    - Smallest safe outcome
    """
    task_name = args.task or input("What task needs scope reduction? ")
    essential = args.essential or input("What's the absolute minimum that must work? ")
    polish = args.polish or input("What can be deferred (polish, nice-to-haves)? ")

    lines = [
        f"# ADHD Coach — Functional Minimums: {task_name}",
        f"Date: {today_str()}",
        "",
        "## Essential (must work)",
        f"- {essential}",
        "",
        "## Deferred (polish / nice-to-have)",
        f"- {polish}",
        "",
        "## Safety constraints (never deferred)",
        "- Data integrity",
        "- Authentication/authorization checks",
        "- Destructive-action confirmation",
        "",
        "## Smallest safe outcome",
        f"The reduced version of '{task_name}' that preserves safety and function,",
        "executed now. Polish comes later as a separate task.",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("minimums", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: decompose — break big tasks
# ---------------------------------------------------------------------------
def cmd_decompose(args):
    """Break big/ambiguous tasks into observable units.

    Table 2 features:
    - Observable definition of done per unit
    - First step under 2 minutes
    - Steps 5–25 minutes with check-in invitations
    - Written checklists to files
    """
    task_name = args.task or input("What big task needs breaking down? ")
    done_def = args.done or input("What does 'done' look like for the whole task? ")

    lines = [
        f"# ADHD Coach — Task Decomposition: {task_name}",
        f"Date: {today_str()}",
        "",
        "## Definition of done (whole task)",
        f"- {done_def}",
        "",
        "## Units (each with observable done criteria)",
        "1. [ ] Unit 1 — done when: __________ (under 2 minutes to start)",
        "2. [ ] Unit 2 — done when: __________ (5–25 minutes)",
        "3. [ ] Unit 3 — done when: __________ (5–25 minutes)",
        "",
        "## Check-ins",
        "- After each unit: mark done, note blocker, decide next unit",
        "- If stuck on a unit for 3 attempts: try a genuinely different strategy",
        "",
        "## Hidden dependencies",
        "- List anything that could block a unit before you start",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("decompose", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: time-estimate — time blindness
# ---------------------------------------------------------------------------
def cmd_time_estimate(args):
    """Time blindness — three-point ranges + stop rules.

    Table 2 features:
    - Best / realistic / worst case ranges
    - Hidden costs, checkpoints, stop rules
    - Single-turn audit, refuses to promise cross-session memory
    """
    task_name = args.task or input("What task needs a time estimate? ")
    best = args.best or input("Best case (optimistic)? ")
    realistic = args.realistic or input("Realistic case? ")
    worst = args.worst or input("Worst case (pessimistic)? ")

    lines = [
        f"# ADHD Coach — Time Estimate: {task_name}",
        f"Date: {today_str()}",
        "",
        "## Three-point estimate",
        f"- Best case: {best}",
        f"- Realistic: {realistic}",
        f"- Worst case: {worst}",
        "",
        "## Hidden costs",
        "- [ ] Setup / context-switching time",
        "- [ ] Interruption buffer",
        "- [ ] Review / fix-up time",
        "",
        "## Checkpoints",
        "- [ ] Checkpoint 1: __________",
        "- [ ] Checkpoint 2: __________",
        "",
        "## Stop rules",
        "- Stop if elapsed time exceeds worst case",
        "- Stop after 3 failed attempts — try a different strategy",
        "",
        "## Note",
        "This is a single-turn estimate. It does not promise cross-session memory.",
        "Re-estimate if context changes significantly.",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("time-estimate", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: choices — indecision
# ---------------------------------------------------------------------------
def cmd_choices(args):
    """Indecision — top 3 options only, rest held back.

    Table 2 features:
    - Top three options only, ranked smallest-effort first
    - Rest held back: "(N more hidden — complete one first)"
    - One-line trade-offs, recommendation first
    """
    decision = args.decision or input("What decision are you stuck on? ")
    option1 = args.option1 or input("Option 1 (smallest effort): ")
    option2 = args.option2 or input("Option 2: ")
    option3 = args.option3 or input("Option 3: ")
    extra = args.extra or input("Additional options (comma-separated, will be hidden): ")

    hidden_count = len([o for o in extra.split(",") if o.strip()])

    lines = [
        f"# ADHD Coach — Choice Reduction: {decision}",
        f"Date: {today_str()}",
        "",
        "## Top 3 options (ranked, smallest effort first)",
        f"1. {option1}",
        f"2. {option2}",
        f"3. {option3}",
    ]
    if hidden_count > 0:
        lines.append(f"")
        lines.append(f"## Hidden ({hidden_count} more — complete one of the above first)")
        lines.append(f"- {extra}")
    lines += [
        "",
        "## Trade-offs (one line each)",
        f"- {option1}: __________",
        f"- {option2}: __________",
        f"- {option3}: __________",
        "",
        "## Recommendation",
        f"Start with: {option1}",
        "",
        "## Rule",
        "One question per message. If stuck, narrow to 2–3 choices with a recommended default.",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("choices", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: setshift — new strategy after 3 failures
# ---------------------------------------------------------------------------
def cmd_setshift(args):
    """Repeating a failed approach — genuinely different strategy after 3 attempts.

    Table 2 features:
    - Force a genuinely different strategy after 3 attempts
    - Same approach × 3 = stop, reassess, change
    """
    task_name = args.task or input("What task have you been stuck on? ")
    attempts = args.attempts or int(input("How many attempts so far? ") or "3")
    current_approach = args.current_approach or input("What approach have you been using? ")

    lines = [
        f"# ADHD Coach — Set Shift: {task_name}",
        f"Date: {today_str()}",
        "",
        "## Current situation",
        f"- Attempts so far: {attempts}",
        f"- Current approach: {current_approach}",
        "",
    ]

    if attempts >= 3:
        lines += [
            "## Threshold reached — switch strategy",
            "You've tried this approach 3+ times. Time for a genuinely different strategy:",
            "",
            "1. What's one assumption in your current approach that might be wrong?",
            "2. What would a completely different first step look like?",
            "3. Can you reduce scope to the smallest safe outcome?",
            "4. Is there a body-doubling or environment change that would help?",
            "",
            "## New approach (write it down)",
            "- ________________________________________",
        ]
    else:
        lines += [
            "## Below threshold",
            f"Continue with current approach. Threshold is 3 attempts; you're at {attempts}.",
            "",
            "## If you hit 3 attempts",
            "Stop, reassess, change strategy — don't repeat the same failing approach.",
        ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("setshift", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: closure — surface >50% complete items
# ---------------------------------------------------------------------------
def cmd_closure(args):
    """Jumping to new work — surface items >50% complete first.

    Table 2 features:
    - Surface near-finished tasks before starting new ones
    - One-tap dismiss
    - Never blocks — surfaces, doesn't commands
    """
    lines = [
        f"# ADHD Coach — Closure Gate",
        f"Date: {today_str()}",
        "",
        "## Items over 50% complete (finish before starting new work)",
        "",
        "1. [ ] Item 1 — ~60% done — one last step: __________",
        "2. [ ] Item 2 — ~70% done — one last step: __________",
        "3. [ ] Item 3 — ~55% done — one last step: __________",
        "",
        "## Rule",
        "Surface near-finished items first. One-tap dismiss — never blocks.",
        "Never jump to new work before checking this list.",
        "",
        "## If nothing is >50% complete",
        "Start the smallest new task (under 2 minutes to begin).",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("closure", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: reanchor — working memory
# ---------------------------------------------------------------------------
def cmd_reanchor(args):
    """Losing the thread — working-memory re-anchor.

    Table 2 features:
    - Proactive re-anchor every 5 turns in sessions over 10
    - Restates active context, original question, current action
    - Working surface: outcome, target, must, must not, authority, done evidence
    """
    lines = [
        f"# ADHD Coach — Working Memory Re-anchor",
        f"Date: {today_str()}",
        "",
        "## Active context",
        "- Original question: __________",
        "- Current action: __________",
        "- Active constraint: __________",
        "",
        "## Constraint ledger",
        "| Field | Value |",
        "|-------|-------|",
        "| Outcome | __________ |",
        "| Target | __________ |",
        "| Must | __________ |",
        "| Must not | __________ |",
        "| Authority | __________ |",
        "| Done evidence | __________ |",
        "",
        "## Re-entry step",
        "If you come back after a break, start here: __________",
        "",
        "## Rule",
        "Proactively re-state context when conversation exceeds 15 turns.",
        "Never ask you to 'keep X in mind'.",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("reanchor", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: inhibit — check actions against goal
# ---------------------------------------------------------------------------
def cmd_inhibit(args):
    """Check actions against goal before significant changes.

    Table 2 features:
    - Check target and negative constraints before significant actions
    - Names drift after 3 adjacent off-goal actions
    - Reversible edits stay silent; irreversible actions need visible intent
    """
    action = args.action or input("What action are you about to take? ")
    target = args.target or input("What's the goal/target this serves? ")

    lines = [
        f"# ADHD Coach — Action Check: {action}",
        f"Date: {today_str()}",
        "",
        "## Target",
        f"- {target}",
        "",
        "## Negative constraints (must not)",
        "- [ ] Does not delete data without confirmation",
        "- [ ] Does not force-push or schema-migrate without backup",
        "- [ ] Does not change authentication/authorization",
        "",
        "## Reversibility",
        "- [ ] Is this action reversible? Yes / No",
        "- [ ] If irreversible: visible intent check required",
        "",
        "## Drift check",
        "Have you taken 3+ adjacent off-goal actions? If yes, stop and re-anchor.",
        "",
        "## Decision",
        f"Proceed with '{action}'? Yes / No / Modify",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("inhibit", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: scaffold — environment redesign
# ---------------------------------------------------------------------------
def cmd_scaffold(args):
    """Redesign environment after repeated failure at point of action.

    Table 2 features:
    - Fires when a known intention keeps failing at the point of action
    - Cues, defaults, tools, support
    - Redesign the environment, not the person
    """
    intention = args.intention or input("What intention keeps failing? ")
    failure_point = args.failure_point or input("Where does it fail (point of action)? ")
    current_cues = args.current_cues or input("What cues/defaults/tools currently exist? ")

    lines = [
        f"# ADHD Coach — Environment Scaffold: {intention}",
        f"Date: {today_str()}",
        "",
        "## Intention",
        f"- {intention}",
        "",
        "## Failure point",
        f"- {failure_point}",
        "",
        "## Current environment",
        f"- Cues/defaults/tools: {current_cues}",
        "",
        "## Redesign",
        "1. Add a cue at the point of action: __________",
        "2. Set a default that requires opt-out: __________",
        "3. Make the tool easier to reach: __________",
        "4. Add support (body-doubling, checklist): __________",
        "",
        "## Rule",
        "Redesign the environment, not the person. The same intention failing",
        "3+ times at the same point means the environment needs changing.",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("scaffold", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Subcommand: velocity — capture:ship ratio
# ---------------------------------------------------------------------------
def cmd_velocity(args):
    """Capture:ship ratio — healthy ~3:1, warn at ≥5:1.

    Table 2 features:
    - ~3:1 is healthy in product work
    - ≥5:1 warns of backlog generating decision paralysis
    - 7-day window, surfaced past 5:1
    """
    captured = args.captured or int(input("Items captured (backlog) in last 7 days? ") or "0")
    shipped = args.shipped or int(input("Items shipped/completed in last 7 days? ") or "0")

    ratio = captured / shipped if shipped > 0 else float("inf")

    status = "healthy"
    if ratio >= 5.0:
        status = "warn — decision paralysis risk"
    elif ratio > 3.0:
        status = "caution"

    lines = [
        f"# ADHD Coach — Velocity Check",
        f"Date: {today_str()}",
        "",
        "## Capture:ship ratio (7-day window)",
        f"- Captured (backlog): {captured}",
        f"- Shipped (completed): {shipped}",
        f"- Ratio: {ratio:.2f}:1",
        "",
        "## Status",
        f"- {status}",
        "",
        "## Interpretation",
        "- ~3:1 is healthy",
        "- ≥5:1 warns of backlog generating decision paralysis",
        "",
        "## Action",
        "- If ≥5:1: reduce capture, increase shipping, or both",
        "- If healthy: continue current cadence",
        "- 7-day rolling window — re-check next week",
    ]

    report = "\n".join(lines)
    print(report)

    if not args.dry_run:
        path = write_report("velocity", report)
        print(f"\nSaved to: {path}")

    return 0


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="ADHD Execution Coach — Table 2 features (coaching in the moment)"
    )
    parser.add_argument("--vault", required=True, help="Vault root path")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Report only, don't write files (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write reports to vault (overrides --dry-run)",
    )
    parser.add_argument("--test", action="store_true", help="Run built-in self-tests")

    sub = parser.add_subparsers(dest="command")

    # Common args
    task_arg = lambda p: p.add_argument("--task", nargs="?", help="Task name")

    p_initiate = sub.add_parser("initiate", help="Can't start — first action + bridges")
    task_arg(p_initiate)
    p_initiate.add_argument("--done", help="Definition of done")

    p_minimums = sub.add_parser("minimums", help="Reduce scope — functional minimums")
    task_arg(p_minimums)
    p_minimums.add_argument("--essential", help="Minimum that must work")
    p_minimums.add_argument("--polish", help="What can be deferred")

    p_decompose = sub.add_parser("decompose", help="Break big tasks into units")
    task_arg(p_decompose)
    p_decompose.add_argument("--done", help="Definition of done")

    p_time = sub.add_parser("time-estimate", help="Time blindness — three-point ranges")
    task_arg(p_time)
    p_time.add_argument("--best", help="Best case estimate")
    p_time.add_argument("--realistic", help="Realistic estimate")
    p_time.add_argument("--worst", help="Worst case estimate")

    p_choices = sub.add_parser("choices", help="Indecision — top 3 options")
    p_choices.add_argument("--decision", nargs="?", help="Decision to make")
    p_choices.add_argument("--option1", help="Option 1 (smallest effort)")
    p_choices.add_argument("--option2", help="Option 2")
    p_choices.add_argument("--option3", help="Option 3")
    p_choices.add_argument("--extra", help="Additional options, comma-separated")

    p_setshift = sub.add_parser("setshift", help="New strategy after 3 failures")
    task_arg(p_setshift)
    p_setshift.add_argument("--attempts", type=int, help="Attempts so far")
    p_setshift.add_argument("--current-approach", help="Current approach being used")

    sub.add_parser("closure", help="Surface items over 50 percent complete")
    sub.add_parser("reanchor", help="Working memory re-anchor")

    p_inhibit = sub.add_parser("inhibit", help="Check action against goal")
    p_inhibit.add_argument("--action", nargs="?", help="Action to check")
    p_inhibit.add_argument("--target", help="Goal this serves")

    p_scaffold = sub.add_parser("scaffold", help="Redesign environment after failure")
    p_scaffold.add_argument("--intention", nargs="?", help="Intention that keeps failing")
    p_scaffold.add_argument("--failure-point", help="Where it fails at point of action")
    p_scaffold.add_argument("--current-cues", help="Current cues/defaults/tools")

    p_velocity = sub.add_parser("velocity", help="Capture:ship ratio")
    p_velocity.add_argument("--captured", type=int, help="Items captured (7 days)")
    p_velocity.add_argument("--shipped", type=int, help="Items shipped (7 days)")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.test:
        return self_test()

    if not args.command:
        parser.print_help()
        return 0

    # Apply overrides dry-run
    dry_run = args.dry_run and not args.apply
    args.dry_run = dry_run

    # Resolve paths (deferred, never at import time)
    init_paths(args.vault)

    dispatch = {
        "initiate": cmd_initiate,
        "minimums": cmd_minimums,
        "decompose": cmd_decompose,
        "time-estimate": cmd_time_estimate,
        "choices": cmd_choices,
        "setshift": cmd_setshift,
        "closure": cmd_closure,
        "reanchor": cmd_reanchor,
        "inhibit": cmd_inhibit,
        "scaffold": cmd_scaffold,
        "velocity": cmd_velocity,
    }

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
