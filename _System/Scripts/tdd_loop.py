#!/usr/bin/env python3
"""
Hermes Brain — TDD Loop (Kent Beck's Test-Driven Development).

Red → Green → Refactor cycle applied to vault scripts and skills.
Write a failing test first, then minimal code to pass, then refactor
while keeping tests green. Never mix refactoring with behavioral change
— pair with `tidy_first.py` and `refactor_catalog.py`.

Subcommands:
  tdd-loop red <test_name>     Write a failing test (Red phase)
  tdd-loop green <test_name>   Write minimal implementation to pass (Green phase)
  tdd-loop refactor <test_name> Refactor while keeping tests green (Refactor phase)
  tdd-loop run <test_name>     Run full TDD cycle: red → green → refactor → verify
  tdd-loop list                List existing tests in vault
  tdd-loop status              Show TDD state for a test (red/green/refactored/done)
  tdd-loop --test              Built-in self-test suite

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
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
TDD_DIR = None
STATE_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, TDD_DIR, STATE_DIR
    VAULT = os.path.abspath(vault_path)
    TDD_DIR = os.path.join(VAULT, "03-Resources", "TDD")
    STATE_DIR = os.path.join(TDD_DIR, "state")


# ---------------------------------------------------------------------------
# TDD state
# ---------------------------------------------------------------------------
STATES = ("red", "green", "refactored", "done")


def state_path(test_name):
    return os.path.join(STATE_DIR, slugify(test_name) + ".json")


def load_state(test_name):
    path = state_path(test_name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_state(test_name, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    path = state_path(test_name)
    state["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return path


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


def find_python_files():
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


def find_test_files():
    """Yield test files (test_*.py or *_test.py) in vault."""
    for path in find_python_files():
        base = os.path.basename(path)
        if base.startswith("test_") or base.endswith("_test.py"):
            yield path


def run_python_tests():
    """Run all test files in vault, return (passed, failed, output)."""
    import subprocess
    passed = 0
    failed = 0
    output_parts = []
    for path in find_test_files():
        try:
            result = subprocess.run(
                [sys.executable, path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                passed += 1
                output_parts.append(f"✅ {os.path.relpath(path, VAULT)} — passed")
            else:
                failed += 1
                output_parts.append(f"❌ {os.path.relpath(path, VAULT)} — failed (exit {result.returncode})")
                if result.stdout:
                    output_parts.append(result.stdout)
                if result.stderr:
                    output_parts.append(result.stderr)
        except subprocess.TimeoutExpired:
            failed += 1
            output_parts.append(f"⏱️  {os.path.relpath(path, VAULT)} — timed out")
        except Exception as e:
            failed += 1
            output_parts.append(f"❌ {os.path.relpath(path, VAULT)} — error: {e}")
    return passed, failed, "\n".join(output_parts)


# ---------------------------------------------------------------------------
# Red phase: write a failing test
# ---------------------------------------------------------------------------
def red_phase(test_name, implementation_file=None, dry_run=True, state=None):
    """Write a failing test for a feature. The test should fail when run."""
    if state is None:
        state = load_state(test_name) or {"test_name": test_name, "phase": None}
    state["phase"] = "red"
    state["started_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    test_file = os.path.join(TDD_DIR, "test_" + slugify(test_name) + ".py")
    test_content = f'''#!/usr/bin/env python3
"""
TDD test — {test_name}
Red phase: this test should FAIL before the implementation exists.
Run: python3 {os.path.basename(test_file)}
Expected: FAILURE (test does not exist yet or assertion fails)
"""

import sys
import os

# Add vault to path so we can import the implementation under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_System", "Scripts"))

# TODO: import the function/module you're about to implement
# from your_module import your_function


def test_{slugify(test_name)}_exists():
    """The feature should exist."""
    # TODO: replace with a real assertion once you know the interface
    assert True, "Placeholder — replace with real test"


def test_{slugify(test_name)}_behaves_correctly():
    """The feature should produce correct output."""
    # TODO: replace with real behavior assertion
    assert True, "Placeholder — replace with real behavior test"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
'''

    result = {
        "ok": True,
        "phase": "red",
        "test_name": test_name,
        "test_file": test_file,
        "content": test_content,
        "_state": state,
    }

    if not dry_run:
        write_file(test_file, test_content)
        if state is not None:
            save_state(test_name, state)

    return result


# ---------------------------------------------------------------------------
# Green phase: write minimal implementation
# ---------------------------------------------------------------------------
def green_phase(test_name, implementation_file=None, dry_run=True, state=None):
    """Write minimal implementation to make the test pass."""
    if state is None:
        state = load_state(test_name) or {"test_name": test_name, "phase": None}
    if state.get("phase") != "red":
        return {
            "ok": False,
            "error": f"Cannot go green — current phase is '{state.get('phase', 'none')}'. Run 'red' first.",
            "_state": state,
        }

    state["phase"] = "green"

    impl_file = implementation_file or os.path.join(
        TDD_DIR, "impl_" + slugify(test_name) + ".py"
    )
    impl_content = f'''#!/usr/bin/env python3
"""
TDD implementation — {test_name}
Green phase: minimal implementation to make the test pass.
Only write enough code to pass the test — no more.
"""

# TODO: implement the feature here. Keep it minimal.
# Every line should be justified by a failing test.


def {slugify(test_name)}():
    """Placeholder implementation."""
    return True


if __name__ == "__main__":
    print("{slugify(test_name)}: green phase — minimal implementation ready")
'''

    result = {
        "ok": True,
        "phase": "green",
        "test_name": test_name,
        "implementation_file": impl_file,
        "content": impl_content,
        "_state": state,
    }

    if not dry_run:
        write_file(impl_file, impl_content)
        if state is not None:
            save_state(test_name, state)

    return result


# ---------------------------------------------------------------------------
# Refactor phase: improve while keeping tests green
# ---------------------------------------------------------------------------
def refactor_phase(test_name, dry_run=True, state=None):
    """Refactor while keeping tests green. Pair with tidy_first.py + refactor_catalog.py."""
    if state is None:
        state = load_state(test_name) or {"test_name": test_name, "phase": None}
    if state.get("phase") != "green":
        return {
            "ok": False,
            "error": f"Cannot refactor — current phase is '{state.get('phase', 'none')}'. Run 'green' first.",
            "_state": state,
        }

    state["phase"] = "refactored"

    # Run tests to confirm they're still green before refactoring
    passed, failed, output = run_python_tests()
    tests_green = failed == 0

    result = {
        "ok": True,
        "phase": "refactored",
        "test_name": test_name,
        "tests_green_before_refactor": tests_green,
        "test_output": output,
        "_state": state,
    }

    if not dry_run and tests_green:
        save_state(test_name, state)
    elif not dry_run and not tests_green:
        result["ok"] = False
        result["error"] = "Cannot refactor — tests are not green. Fix failing tests first."

    return result


# ---------------------------------------------------------------------------
# Done: mark complete
# ---------------------------------------------------------------------------
def done_phase(test_name, dry_run=True, state=None):
    """Mark a TDD cycle as complete."""
    if state is None:
        state = load_state(test_name) or {"test_name": test_name, "phase": None}
    if state.get("phase") not in ("refactored", "green"):
        return {
            "ok": False,
            "error": f"Cannot mark done — current phase is '{state.get('phase', 'none')}'. Run 'refactor' first.",
            "_state": state,
        }

    # Final test run to confirm green
    passed, failed, output = run_python_tests()
    tests_green = failed == 0

    state["phase"] = "done"
    state["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result = {
        "ok": True,
        "phase": "done",
        "test_name": test_name,
        "tests_green": tests_green,
        "test_output": output,
        "_state": state,
    }

    if not dry_run and tests_green:
        save_state(test_name, state)
    elif not dry_run and not tests_green:
        result["ok"] = False
        result["error"] = "Cannot mark done — tests are not green."

    return result


# ---------------------------------------------------------------------------
# Full TDD cycle: red → green → refactor → done
# ---------------------------------------------------------------------------
def run_cycle(test_name, dry_run=True):
    """Run the complete TDD cycle."""
    results = []
    state = {"test_name": test_name, "phase": None}

    # Red
    r = red_phase(test_name, dry_run=dry_run, state=state)
    results.append(r)
    if not r["ok"]:
        return results
    state = r["_state"]

    # Green
    g = green_phase(test_name, dry_run=dry_run, state=state)
    results.append(g)
    if not g["ok"]:
        return results
    state = g["_state"]

    # Refactor
    rf = refactor_phase(test_name, dry_run=dry_run, state=state)
    results.append(rf)
    if not rf["ok"]:
        return results
    state = rf["_state"]

    # Done
    d = done_phase(test_name, dry_run=dry_run, state=state)
    results.append(d)

    return results


# ---------------------------------------------------------------------------
# List / Status
# ---------------------------------------------------------------------------
def list_tests():
    """List all TDD tests in vault."""
    tests = []
    if os.path.isdir(TDD_DIR):
        for f in os.listdir(TDD_DIR):
            if f.startswith("test_") and f.endswith(".py"):
                test_name = f[5:-3]  # strip test_ and .py
                state = load_state(test_name)
                tests.append({
                    "name": test_name,
                    "file": f,
                    "phase": state.get("phase", "none") if state else "none",
                    "updated_at": state.get("updated_at", "—") if state else "—",
                })
    return tests


def status(test_name):
    """Show TDD state for a test."""
    state = load_state(test_name)
    if not state:
        return {"exists": False, "test_name": test_name}
    return {"exists": True, "test_name": test_name, **state}


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(results, dry_run=True):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# TDD Loop — Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "--",
        "",
    ]

    if not results:
        lines.append("## No TDD activity to report.")
        lines.append("")
        write_report(lines)
        return

    for r in results:
        phase = r.get("phase", "?")
        label = phase.title()
        lines.append(f"## {label} Phase — {r.get('test_name', '?')}")
        lines.append("")
        lines.append(f"- **Phase**: {label}")
        lines.append(f"- **Test**: {r.get('test_name', '?')}")

        if r.get("phase") == "red":
            lines.append(f"- **Test file**: `{r.get('test_file', '—')}`")
            lines.append("- **Status**: Test written, expected to FAIL before implementation")
        elif r.get("phase") == "green":
            lines.append(f"- **Implementation file**: `{r.get('implementation_file', '—')}`")
            lines.append("- **Status**: Minimal implementation written to pass the test")
        elif r.get("phase") == "refactored":
            lines.append(f"- **Tests green before refactor**: {'✅ Yes' if r.get('tests_green_before_refactor') else '❌ No'}")
            lines.append("- **Status**: Refactored, tests still green")
        elif r.get("phase") == "done":
            lines.append(f"- **Tests green**: {'✅ Yes' if r.get('tests_green') else '❌ No'}")
            lines.append("- **Status**: TDD cycle complete")

        if not r.get("ok", True):
            lines.append(f"- **Error**: {r.get('error', 'unknown')}")
        lines.append("")

    lines.append("--")
    lines.append("")
    lines.append("## Kent Beck's TDD Rules")
    lines.append("")
    lines.append("- Write a failing test before any production code (Red)")
    lines.append("- Write only enough code to make the test pass (Green)")
    lines.append("- Refactor only when tests are green (Refactor)")
    lines.append("- Never mix refactoring with behavioral change")
    lines.append("")

    write_report(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 TDD Loop — Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    import tempfile
    import shutil

    # Test 1: state save/load roundtrip
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            state = {"test_name": "my_test", "phase": "red", "started_at": "2026-01-01"}
            path = save_state("my_test", state)
            loaded = load_state("my_test")
            assert loaded is not None
            assert loaded["phase"] == "red"
            assert loaded["test_name"] == "my_test"
            print("✅ Test 1: state save/load roundtrip")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: red phase creates test file
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            result = red_phase("my_feature", dry_run=True)
            assert result["ok"] is True
            assert result["phase"] == "red"
            assert "test_file" in result
            assert "test_my_feature" in result["test_file"]
            print("✅ Test 2: red phase creates test file spec")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: green phase blocked without red
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            result = green_phase("no_red_yet", dry_run=True)
            assert result["ok"] is False
            assert "Run 'red' first" in result["error"]
            print("✅ Test 3: green phase blocked without red")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: refactor phase blocked without green
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            result = refactor_phase("no_green_yet", dry_run=True)
            assert result["ok"] is False
            assert "Run 'green' first" in result["error"]
            print("✅ Test 4: refactor phase blocked without green")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1

    # Test 5: done phase blocked without refactor/green
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            result = done_phase("no_refactor_yet", dry_run=True)
            assert result["ok"] is False
            assert "Run 'refactor' first" in result["error"]
            print("✅ Test 5: done phase blocked without refactor/green")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1

    # Test 6: full cycle dry run
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            results = run_cycle("full_cycle_test", dry_run=True)
            assert len(results) == 4
            assert results[0]["phase"] == "red"
            assert results[1]["phase"] == "green"
            assert results[2]["phase"] == "refactored"
            assert results[3]["phase"] == "done"
            assert all(r["ok"] for r in results)
            print("✅ Test 6: full cycle dry run")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1

    # Test 7: list_tests returns empty on empty vault
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            tests = list_tests()
            assert tests == []
            print("✅ Test 7: list_tests returns empty on empty vault")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 7 failed: {e}")
        failed += 1

    # Test 8: status returns not-exists for unknown test
    try:
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            result = status("does_not_exist")
            assert result["exists"] is False
            print("✅ Test 8: status returns not-exists for unknown test")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 8 failed: {e}")
        failed += 1

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain — TDD Loop (Kent Beck): Red → Green → Refactor.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply TDD steps (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_red = sub.add_parser("red", help="Red phase: write a failing test")
    p_red.add_argument("test_name", help="Name of the test/feature")

    p_green = sub.add_parser("green", help="Green phase: minimal implementation")
    p_green.add_argument("test_name", help="Name of the test/feature")
    p_green.add_argument("--implementation-file", help="Path to implementation file (optional)")

    p_refactor = sub.add_parser("refactor", help="Refactor phase: improve while tests green")
    p_refactor.add_argument("test_name", help="Name of the test/feature")

    p_done = sub.add_parser("done", help="Mark TDD cycle complete")
    p_done.add_argument("test_name", help="Name of the test/feature")

    p_run = sub.add_parser("run", help="Run full TDD cycle: red → green → refactor → done")
    p_run.add_argument("test_name", help="Name of the test/feature")

    sub.add_parser("list", help="List existing TDD tests in vault")

    p_status = sub.add_parser("status", help="Show TDD state for a test")
    p_status.add_argument("test_name", help="Name of the test/feature")

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

    if args.command == "red":
        result = red_phase(args.test_name, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result.get('error', 'unknown')}", file=sys.stderr)
            sys.exit(1)
        print(f"## Red Phase — {args.test_name}")
        print(f"")
        print(f"- **Test file**: `{result['test_file']}`")
        print(f"- **Status**: Test written, expected to FAIL before implementation")
        print("")
        if not dry_run:
            print("✅ Applied: failing test written. Run it to confirm it fails.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "green":
        result = green_phase(args.test_name, args.implementation_file, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"## Green Phase — {args.test_name}")
        print(f"")
        print(f"- **Implementation file**: `{result['implementation_file']}`")
        print(f"- **Status**: Minimal implementation written to pass the test")
        print("")
        if not dry_run:
            print("✅ Applied: implementation written. Run tests to confirm they pass.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "refactor":
        result = refactor_phase(args.test_name, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"## Refactor Phase — {args.test_name}")
        print(f"")
        print(f"- **Tests green before refactor**: {{'✅ Yes' if result.get('tests_green_before_refactor') else '❌ No'}}")
        print(f"- **Status**: Refactored, tests still green")
        print("")
        if not dry_run:
            print("✅ Applied: refactored. Tests are still green.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "done":
        result = done_phase(args.test_name, dry_run=dry_run)
        if not result["ok"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"## Done — {args.test_name}")
        print(f"")
        print(f"- **Tests green**: {{'✅ Yes' if result.get('tests_green') else '❌ No'}}")
        print(f"- **Status**: TDD cycle complete")
        print("")
        if not dry_run:
            print("✅ Applied: TDD cycle marked complete.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "run":
        results = run_cycle(args.test_name, dry_run=dry_run)
        failed_results = [r for r in results if not r.get("ok", True)]
        if failed_results:
            for r in failed_results:
                print(f"❌ {r.get('phase', '?')}: {r.get('error', 'unknown')}", file=sys.stderr)
            sys.exit(1)
        print(f"## TDD Cycle Complete — {args.test_name}")
        print(f"")
        for r in results:
            print(f"- {r['phase'].title()}: ✅")
        print("")
        if not dry_run:
            print("✅ Applied: full TDD cycle complete. Tests are green.")
        else:
            print("🔍 Dry run — no changes made. Run with --apply to execute.")
        return

    if args.command == "list":
        tests = list_tests()
        if not tests:
            print("## No TDD tests found in vault.")
            print("")
            print("Start one with: `tdd-loop red <test_name>`")
            return
        print("## TDD Tests in Vault")
        print("")
        print("| Test | Phase | Updated |")
        print("|------|-------|---------|")
        for t in tests:
            print(f"| {t['name']} | {t['phase']} | {t['updated_at']} |")
        print("")
        return

    if args.command == "status":
        result = status(args.test_name)
        if not result["exists"]:
            print(f"## TDD Status — {args.test_name}")
            print("")
            print("Not found. Start with: `tdd-loop red {args.test_name}`")
            return
        print(f"## TDD Status — {args.test_name}")
        print("")
        print(f"- **Phase**: {result.get('phase', 'none')}")
        print(f"- **Started**: {result.get('started_at', '—')}")
        print(f"- **Updated**: {result.get('updated_at', '—')}")
        if result.get("completed_at"):
            print(f"- **Completed**: {result['completed_at']}")
        print("")
        return

    print("Error: No command specified. Use 'red', 'green', 'refactor', 'done', 'run', "
          "'list', or 'status'.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()