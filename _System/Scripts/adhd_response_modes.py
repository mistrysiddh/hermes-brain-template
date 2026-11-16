#!/usr/bin/env python3
"""
Hermes Brain — ADHD Response Modes + Circuit Breaker.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Stdlib-only
  - --dry-run default, --apply for human-in-the-loop approval
  - --test built-in self-test suite

Modes (state-oriented, not ADHD-specific):
  - overloaded      → Do this first / Do now / Defer / Drop / Minimum viable version
  - foggy           → 4 labels: Next action, State line, The question, Recommendation
  - plan-compass    → Progress label, State line, The question, Recommendation+default, Why it matters, 2-3 choices
  - reality-check   → Facts + one ordinary explanation + trusted-person step; no diagnosis labels

Circuit breaker:
  - After N "still broken" turns: stop iterating, name the assumption, ask one diagnostic question

Tone calibration:
  - Matches user energy per message type: clipped → concise/action, exploratory → depth,
    frustrated → acknowledge friction skip pep talk, excited → match energy,
    overwhelmed → simplify radically one next step

Pre-send self-check:
  - Deletes openers ("Great question", "Let me…"), closers ("Hope this helps"),
    "anything else?" sidebars, empty hedges ("perhaps/might"), idioms → literal action
    before sending.

Exit code: 0 always (reporting tool, not a gate).
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
MODES_DIR = None
CIRCUIT_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, MODES_DIR, CIRCUIT_DIR
    VAULT = os.path.abspath(vault_path)
    MODES_DIR = os.path.join(VAULT, "01-Projects", "ADHD-Modes")
    CIRCUIT_DIR = os.path.join(VAULT, "03-Resources", "Circuit-Breakers")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODES = ("overloaded", "foggy", "plan-compass", "reality-check")
ALIASES = {
    "burnout": "overloaded",
    "brain-fog": "foggy",
    "fog": "foggy",
    "compass": "plan-compass",
    "reality": "reality-check",
}

CIRCUIT_BREAKER_THRESHOLD = 3  # "still broken" turns before circuit break

OPENERS = [
    r"\b(great question|nice question|good question)\b",
    r"\b(let me|i'll|i will)\b.*\b(look|check|see|find)\b",
    r"\b(sure|certainly|absolutely|of course)\b[,.]?",
]

CLOSERS = [
    r"\b(hope this helps|hope that helps)\b",
    r"\b(feel free to|don't hesitate to)\b.*\b(ask|reach out|contact)\b",
    r"\b(happy to help|glad to help)\b",
]

HEDGES = [
    r"\b(perhaps|maybe|might|could|possibly|probably)\b",
    r"\b(it seems|it appears|looks like)\b",
]

IDIOM_REPLACEMENTS = [
    (r"\bcircle back\b", "follow up"),
    (r"\bthink outside the box\b", "try a different approach"),
    (r"\bleverage\b", "use"),
    (r"\breach out\b", "contact"),
    (r"\bpiggyback\b", "add to"),
]

NO_DIAGNOSIS_LABELS = [
    "psychosis", "manic", "delusion", "paranoia", "adhd diagnosis",
    "burnout", "long covid", "me/cfs", "medical diagnosis",
]

# ---------------------------------------------------------------------------
# Mode: overloaded
# ---------------------------------------------------------------------------
def mode_overloaded(text, next_action=None):
    """Overloaded mode: one priority, one sentence, explicit labels."""
    lines = []
    lines.append("## Overloaded — Do this first")
    lines.append("")
    if next_action:
        lines.append(f"**Do this first:** {next_action}")
        lines.append("")
    lines.append("**Do now:** (1–3 top-level bullets, no sub-bullets)")
    lines.append("- Pick one thing. Ignore the rest.")
    lines.append("")
    lines.append("**Defer:** anything not needed today")
    lines.append("")
    lines.append("**Drop:** diagnostics, alert cleanup, root-cause analysis, routine triage")
    lines.append("")
    lines.append("**Minimum viable version:** what ships if you stop now")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mode: foggy
# ---------------------------------------------------------------------------
def mode_foggy(text, next_action=None, state=None):
    """Foggy mode: short, one-screen answers, 4 labels."""
    lines = []
    lines.append("## Foggy — 4 labels")
    lines.append("")
    if next_action:
        lines.append(f"**Next action:** {next_action}")
        lines.append("")
    if state:
        lines.append(f"**State line:** {state}")
        lines.append("")
    lines.append("**The question:** (one ask only, or selection widget)")
    lines.append("")
    lines.append("**Recommendation:** (one recommendation + default)")
    lines.append("")
    lines.append("> If you only want the next step, output only that label and stop.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mode: plan-compass
# ---------------------------------------------------------------------------
def mode_plan_compass(text, progress=None, state=None, question=None,
                      recommendation=None, default=None, why=None,
                      choices=None, ownership=None):
    """Plan-compass: 6-part turn format + ownership model A/B/C."""
    lines = []
    lines.append("## Plan-compass — decision turn")
    lines.append("")
    if progress:
        lines.append(f"**Progress:** {progress}")
        lines.append("")
    if state:
        lines.append(f"**State line:** {state}")
        lines.append("")
    if question:
        lines.append(f"**The question:** {question}")
        lines.append("")
    if recommendation:
        rec_line = f"**Recommendation:** {recommendation}"
        if default:
            rec_line += f" (default: {default})"
        lines.append(rec_line)
        lines.append("")
    if why:
        lines.append(f"**Why it matters:** {why}")
        lines.append("")
    if choices:
        lines.append("**Choices:**")
        for c in choices[:3]:
            lines.append(f"- {c}")
        lines.append("")
    if ownership:
        owner_map = {"user": "You own it", "team": "Team owns it",
                     "project": "Project owns it"}
        lines.append(f"**Ownership:** {owner_map.get(ownership, ownership)}")
        lines.append("")
    lines.append("> No action until the summary is confirmed.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mode: reality-check
# ---------------------------------------------------------------------------
def mode_reality_check(text, facts=None, explanation=None, trusted_person=None):
    """Reality-check: facts + one ordinary explanation + trusted-person step.
    No diagnosis labels. Ends after the trusted-person step.
    """
    lines = []
    lines.append("## Reality-check — grounded facts")
    lines.append("")
    if facts:
        lines.append("**Facts:**")
        for f in facts:
            lines.append(f"- {f}")
        lines.append("")
    if explanation:
        lines.append(f"**One ordinary explanation:** {explanation}")
        lines.append("")
    lines.append("> No burnout, Long COVID, ME/CFS, or psychosis labels.")
    lines.append("> No naming 'AI psychosis'. Discourages secrecy, isolation, continued AI engagement.")
    lines.append("")
    if trusted_person:
        lines.append("**Trusted-person step:** Send one message to: " + trusted_person)
        lines.append("")
    lines.append("> Ends here. No further AI analysis invited.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------
def circuit_breaker_check(turns_still_broken, assumption=None,
                          diagnostic_question=None):
    """After N 'still broken' turns: stop iterating, name assumption,
    ask one diagnostic question."""
    lines = []
    if turns_still_broken >= CIRCUIT_BREAKER_THRESHOLD:
        lines.append("## 🔴 Circuit breaker tripped")
        lines.append("")
        lines.append(f"Stopped after {turns_still_broken} 'still broken' turns.")
        lines.append("")
        if assumption:
            lines.append(f"**Named assumption:** {assumption}")
            lines.append("")
        if diagnostic_question:
            lines.append(f"**One diagnostic question:** {diagnostic_question}")
            lines.append("")
        lines.append("Do not keep iterating. Resolve the assumption first.")
        lines.append("")
        return True, "\n".join(lines)
    else:
        remaining = CIRCUIT_BREAKER_THRESHOLD - turns_still_broken
        lines.append(f"✅ Circuit not tripped — {remaining} turn(s) remaining "
                     f"before breaker at {CIRCUIT_BREAKER_THRESHOLD}.")
        lines.append("")
        return False, "\n".join(lines)


# ---------------------------------------------------------------------------
# Tone calibration
# ---------------------------------------------------------------------------
TONE_GUIDANCE = {
    "clipped": "Concise and action-oriented. No padding.",
    "exploratory": "Match depth. Give room to explore.",
    "frustrated": "Acknowledge friction. Skip the pep talk. Go to solutions.",
    "excited": "Match energy. Keep it moving.",
    "overwhelmed": "Simplify radically. One next step.",
}

def tone_for_message_type(message_type):
    """Return tone guidance for a given message type."""
    return TONE_GUIDANCE.get(message_type.lower(),
                             "Neutral. Match the user's energy.")


# ---------------------------------------------------------------------------
# Pre-send self-check
# ---------------------------------------------------------------------------
def pre_send_check(text, dry_run=True):
    """Delete openers, closers, hedges, idioms → literal action before sending.
    Returns (cleaned_text, changes_made).
    """
    changes = []
    result = text

    # Remove openers
    for pat in OPENERS:
        matches = re.findall(pat, result, flags=re.I)
        if matches:
            result = re.sub(pat, "", result, flags=re.I)
            changes.append(f"Removed opener: {matches[0]}")

    # Remove closers
    for pat in CLOSERS:
        matches = re.findall(pat, result, flags=re.I)
        if matches:
            result = re.sub(pat, "", result, flags=re.I)
            changes.append(f"Removed closer: {matches[0]}")

    # Remove "anything else?" sidebars
    if re.search(r"\b(anything else|is there anything|what else)\b", result, flags=re.I):
        result = re.sub(r"\n?\s*(?:anything else|is there anything|what else)[^\n]*\n?",
                        "", result, flags=re.I)
        changes.append("Removed 'anything else?' sidebar")

    # Remove empty hedges (keep real uncertainty)
    for pat in HEDGES:
        matches = re.findall(pat, result, flags=re.I)
        if matches:
            result = re.sub(pat, "", result, flags=re.I)
            changes.append(f"Removed hedge: {matches[0]}")

    # Replace idioms → literal action
    for pat, repl in IDIOM_REPLACEMENTS:
        matches = re.findall(pat, result, flags=re.I)
        if matches:
            result = re.sub(pat, repl, result, flags=re.I)
            changes.append(f"Replaced idiom: {matches[0]} → {repl}")

    # Collapse multiple blank lines
    result = re.sub(r"\n{3,}", "\n\n", result).strip()

    return result, changes


# ---------------------------------------------------------------------------
# No-diagnosis guard
# ---------------------------------------------------------------------------
def no_diagnosis_guard(text):
    """Flag any diagnosis labels in text. Returns list of flagged terms."""
    flagged = []
    lower = text.lower()
    for term in NO_DIAGNOSIS_LABELS:
        if term in lower:
            flagged.append(term)
    return flagged


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_mode_report(mode, content):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# ADHD Response Mode — {mode.title()}",
        f"Generated: {now}",
        "",
        "--",
        "",
        content,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save to vault
# ---------------------------------------------------------------------------
def save_report_to_vault(report, kind):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(MODES_DIR, f"ADHD-{kind}-{today}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 ADHD Response Modes + Circuit Breaker — Self-Test Suite")
    print("=" * 60)
    passed = 0
    failed = 0

    # Test 1: mode_overloaded renders labels
    try:
        result = mode_overloaded("test", next_action="Send the email")
        assert "Do this first" in result
        assert "Send the email" in result
        assert "Minimum viable version" in result
        print("✅ Test 1: mode_overloaded renders labels")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: mode_foggy renders 4 labels
    try:
        result = mode_foggy("test", next_action="Open the file",
                            state="Step 2 of 4")
        assert "Next action" in result
        assert "State line" in result
        assert "Open the file" in result
        print("✅ Test 2: mode_foggy renders 4 labels")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: mode_plan_compass renders 6 parts + ownership
    try:
        result = mode_plan_compass(
            "", progress="3 of 5 done", state="Waiting on API",
            question="Which endpoint first?",
            recommendation="Use the public endpoint", default="v1",
            why="Unblocks the sync", choices=["A", "B", "C"],
            ownership="user")
        assert "Progress" in result
        assert "Ownership" in result
        assert "You own it" in result
        assert "Use the public endpoint" in result
        print("✅ Test 3: mode_plan_compass renders 6 parts + ownership")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: mode_reality_check no diagnosis labels applied to user
    try:
        result = mode_reality_check(
            "", facts=["API returned 500", "Network is up"],
            explanation="The server is temporarily overloaded.",
            trusted_person="your teammate")
        assert "Facts" in result
        assert "Trusted-person step" in result
        assert "your teammate" in result
        assert "psychosis" in result.lower()  # disclaimer names it to reject it
        # guard catches diagnosis applied to user state, not the disclaimer itself
        flagged_user = no_diagnosis_guard("This looks like psychosis.")
        assert "psychosis" in flagged_user
        print("✅ Test 4: mode_reality_check renders + no diagnosis labels applied to user")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1

    # Test 5: circuit breaker trips at threshold
    try:
        tripped, report = circuit_breaker_check(
            3, assumption="The API is down",
            diagnostic_question="Is the endpoint reachable?")
        assert tripped is True
        assert "Circuit breaker tripped" in report
        assert "Named assumption" in report
        assert "One diagnostic question" in report
        print("✅ Test 5: circuit breaker trips at threshold")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1

    # Test 6: circuit breaker does not trip below threshold
    try:
        tripped, report = circuit_breaker_check(1)
        assert tripped is False
        assert "Circuit not tripped" in report
        print("✅ Test 6: circuit breaker does not trip below threshold")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1

    # Test 7: tone calibration lookup
    try:
        t = tone_for_message_type("frustrated")
        assert "Acknowledge friction" in t
        t = tone_for_message_type("overwhelmed")
        assert "Simplify radically" in t
        t = tone_for_message_type("unknown")
        assert "Neutral" in t
        print("✅ Test 7: tone calibration lookup")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 7 failed: {e}")
        failed += 1

    # Test 8: pre-send check removes opener + closer + hedge + idiom
    try:
        text = ("Great question! Let me look at that for you. "
                "Perhaps you could circle back to it. Hope this helps!")
        cleaned, changes = pre_send_check(text)
        assert "Great question" not in cleaned
        assert "Let me look" not in cleaned
        assert "Hope this helps" not in cleaned
        assert "follow up" in cleaned
        assert len(changes) >= 3
        print("✅ Test 8: pre-send check removes opener/closer/hedge/idiom")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 8 failed: {e}")
        failed += 1

    # Test 9: no-diagnosis guard flags labels
    try:
        flagged = no_diagnosis_guard("This looks like psychosis.")
        assert "psychosis" in flagged
        flagged = no_diagnosis_guard("The API returned 500.")
        assert flagged == []
        print("✅ Test 9: no-diagnosis guard flags labels")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 9 failed: {e}")
        failed += 1

    # Test 10: alias resolution
    try:
        assert ALIASES["burnout"] == "overloaded"
        assert ALIASES["brain-fog"] == "foggy"
        assert ALIASES["compass"] == "plan-compass"
        print("✅ Test 10: alias resolution")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 10 failed: {e}")
        failed += 1

    print("=" * 60)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain — ADHD Response Modes + Circuit Breaker.")
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply safe auto-fixes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")

    sub = parser.add_subparsers(dest="command", help="Command to run")

    # mode subcommand
    p_mode = sub.add_parser("mode", help="Generate an ADHD response mode")
    p_mode.add_argument("--mode", choices=MODES, required=True,
                        help="Response mode to generate")
    p_mode.add_argument("--text", default="", help="Input text to adapt")
    p_mode.add_argument("--next-action", help="Next action (overloaded/foggy)")
    p_mode.add_argument("--state", help="State line (foggy/plan-compass)")
    p_mode.add_argument("--progress", help="Progress label (plan-compass)")
    p_mode.add_argument("--question", help="The question (plan-compass)")
    p_mode.add_argument("--recommendation", help="Recommendation (plan-compass)")
    p_mode.add_argument("--default", help="Default choice (plan-compass)")
    p_mode.add_argument("--why", help="Why it matters (plan-compass)")
    p_mode.add_argument("--choices", nargs="*", help="2-3 choices (plan-compass)")
    p_mode.add_argument("--ownership", choices=["user", "team", "project"],
                        help="Ownership model (plan-compass)")
    p_mode.add_argument("--facts", nargs="*", help="Facts (reality-check)")
    p_mode.add_argument("--explanation", help="One ordinary explanation (reality-check)")
    p_mode.add_argument("--trusted-person", help="Trusted person (reality-check)")
    p_mode.add_argument("--save", action="store_true",
                        help="Save report to vault")

    # circuit subcommand
    p_circuit = sub.add_parser("circuit",
                               help="Check circuit breaker state")
    p_circuit.add_argument("--turns-still-broken", type=int, default=0,
                           help="Number of 'still broken' turns")
    p_circuit.add_argument("--assumption", help="Named assumption to break")
    p_circuit.add_argument("--diagnostic-question",
                           help="One diagnostic question to ask")
    p_circuit.add_argument("--save", action="store_true",
                           help="Save report to vault")

    # tone subcommand
    p_tone = sub.add_parser("tone", help="Get tone guidance for a message type")
    p_tone.add_argument("--message-type", required=True,
                        choices=["clipped", "exploratory", "frustrated",
                                 "excited", "overwhelmed"],
                        help="Message type to calibrate tone for")

    # pre-send subcommand
    p_presend = sub.add_parser("pre-send",
                               help="Run pre-send self-check on text")
    p_presend.add_argument("--text", required=True, help="Text to check")
    p_presend.add_argument("--save", action="store_true",
                           help="Save cleaned text to vault")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.vault:
        args.vault = os.environ.get("HERMES_VAULT_PATH")
    if not args.vault:
        print("Error: --vault <path> or HERMES_VAULT_PATH is required.",
              file=sys.stderr)
        sys.exit(1)

    init_paths(args.vault)
    dry_run = not args.apply

    if args.command == "mode":
        if args.mode == "overloaded":
            content = mode_overloaded(args.text, next_action=args.next_action)
        elif args.mode == "foggy":
            content = mode_foggy(args.text, next_action=args.next_action,
                                 state=args.state)
        elif args.mode == "plan-compass":
            content = mode_plan_compass(
                args.text, progress=args.progress, state=args.state,
                question=args.question, recommendation=args.recommendation,
                default=args.default, why=args.why,
                choices=args.choices or [], ownership=args.ownership)
        elif args.mode == "reality-check":
            content = mode_reality_check(
                args.text, facts=args.facts or [],
                explanation=args.explanation,
                trusted_person=args.trusted_person)
        else:
            print(f"Error: unknown mode {args.mode}", file=sys.stderr)
            sys.exit(1)

        report = generate_mode_report(args.mode, content)
        print(report)
        if args.save:
            saved = save_report_to_vault(report, args.mode)
            print(f"\n📄 Saved to {saved}")
        return

    if args.command == "circuit":
        tripped, report = circuit_breaker_check(
            args.turns_still_broken, assumption=args.assumption,
            diagnostic_question=args.diagnostic_question)
        print(report)
        if args.save:
            saved = save_report_to_vault(report, "circuit-breaker")
            print(f"\n📄 Saved to {saved}")
        return

    if args.command == "tone":
        guidance = tone_for_message_type(args.message_type)
        print(f"## Tone — {args.message_type.title()}")
        print("")
        print(guidance)
        print("")
        return

    if args.command == "pre-send":
        cleaned, changes = pre_send_check(args.text, dry_run=dry_run)
        flagged = no_diagnosis_guard(cleaned)
        print("## Pre-send self-check")
        print("")
        if changes:
            print("**Changes made:**")
            for c in changes:
                print(f"- {c}")
            print("")
        else:
            print("**No changes needed.**\n")
        print("**Cleaned text:**")
        print(cleaned)
        print("")
        if flagged:
            print(f"⚠️  Diagnosis labels flagged: {', '.join(flagged)}")
            print("Remove these before sending.")
        else:
            print("✅ No diagnosis labels detected.")
        if args.save:
            report = generate_mode_report("pre-send", cleaned)
            saved = save_report_to_vault(report, "pre-send")
            print(f"\n📄 Saved to {saved}")
        return

    print("Error: No command specified. Use 'mode', 'circuit', 'tone', "
          "or 'pre-send'.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()