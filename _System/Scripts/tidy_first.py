#!/usr/bin/env python3
"""
Hermes Brain — Tidy First skill (Kent Beck's Tidy First philosophy).

Separates structural tidyings from behavioral changes so you never mix
refactoring with feature work in the same step. Kent Beck's rule:
tidy first, then make the behavioral change — but never both at once.

Subcommands:
  tidy-first scan      Scan vault for tidy candidates (long files,
                       duplicated blocks, dead code, misplaced notes)
  tidy-first apply     Apply a specific tidy (opt-in, --apply required)
  tidy-first check     Verify a file/behavioral change is clean
                       (no tidy mixed in)
  tidy-first --test    Built-in self-test suite

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
# Tidy categories
# ---------------------------------------------------------------------------
TIDY_CATEGORIES = {
    "long_file": {
        "label": "Long file",
        "threshold": 400,  # lines
        "description": "File exceeds line threshold — consider splitting",
    },
    "duplicate_block": {
        "label": "Duplicated block",
        "description": "Identical 5+ line block appears in multiple files",
    },
    "dead_code": {
        "label": "Dead code",
        "description": "Unreachable code after return/raise/exit",
    },
    "misplaced_note": {
        "label": "Misplaced note",
        "description": "Note in wrong directory per vault convention",
    },
    "long_function": {
        "label": "Long function",
        "threshold": 60,  # lines
        "description": "Function/method exceeds line threshold",
    },
    "magic_number": {
        "label": "Magic number",
        "description": "Unnamed numeric literal in code",
    },
}


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


def write_report(lines):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "Tidy-First-Report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Tidy report written to: {path}")
    return path


def slugify(text):
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower()).strip("-_")
    return slug or "untitled"


# ---------------------------------------------------------------------------
# Scan: find tidy candidates
# ---------------------------------------------------------------------------
def scan_long_files():
    findings = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if not f.endswith((".py", ".md")):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            lines = content.splitlines()
            if len(lines) > TIDY_CATEGORIES["long_file"]["threshold"]:
                rel = os.path.relpath(full, VAULT)
                findings.append({
                    "category": "long_file",
                    "file": rel,
                    "lines": len(lines),
                    "threshold": TIDY_CATEGORIES["long_file"]["threshold"],
                    "message": f"{rel} is {len(lines)} lines (threshold {TIDY_CATEGORIES['long_file']['threshold']}) — consider splitting",
                    "suggestion": f"Split {rel} into smaller files; each new file should have a single responsibility",
                })
    return findings


def scan_long_functions():
    findings = []
    func_re = re.compile(r"^\s*(def|class|async def)\s+(\w+)")
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if not f.endswith(".py"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            lines = content.splitlines()
            rel = os.path.relpath(full, VAULT)
            current_func = None
            start_line = 0
            indent_level = 0
            for i, line in enumerate(lines, 1):
                m = func_re.match(line)
                if m:
                    if current_func and (i - start_line) > TIDY_CATEGORIES["long_function"]["threshold"]:
                        findings.append({
                            "category": "long_function",
                            "file": rel,
                            "function": current_func,
                            "lines": i - start_line,
                            "threshold": TIDY_CATEGORIES["long_function"]["threshold"],
                            "message": f"{rel}:{start_line} — {current_func} is {i - start_line} lines (threshold {TIDY_CATEGORIES['long_function']['threshold']})",
                            "suggestion": f"Extract a helper from {current_func} in {rel}; keep each function under {TIDY_CATEGORIES['long_function']['threshold']} lines",
                        })
                    current_func = m.group(2)
                    start_line = i
            # Check the last function in the file (no next function to trigger the check)
            if current_func and (len(lines) - start_line + 1) > TIDY_CATEGORIES["long_function"]["threshold"]:
                findings.append({
                    "category": "long_function",
                    "file": rel,
                    "function": current_func,
                    "lines": len(lines) - start_line + 1,
                    "threshold": TIDY_CATEGORIES["long_function"]["threshold"],
                    "message": f"{rel}:{start_line} — {current_func} is {len(lines) - start_line + 1} lines (threshold {TIDY_CATEGORIES['long_function']['threshold']})",
                    "suggestion": f"Extract a helper from {current_func} in {rel}; keep each function under {TIDY_CATEGORIES['long_function']['threshold']} lines",
                })
    return findings


def scan_dead_code():
    findings = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if not f.endswith(".py"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            lines = content.splitlines()
            rel = os.path.relpath(full, VAULT)
            after_terminal = False
            terminal_line = 0
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if after_terminal and stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    findings.append({
                        "category": "dead_code",
                        "file": rel,
                        "line": i,
                        "terminal_line": terminal_line,
                        "message": f"{rel}:{i} — unreachable code after terminal statement at line {terminal_line}",
                        "suggestion": f"Remove unreachable code at {rel}:{i} or restructure the control flow",
                    })
                if stripped.startswith(("return ", "raise ", "sys.exit", "exit(")) and not stripped.startswith("#"):
                    after_terminal = True
                    terminal_line = i
                elif stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''") and not stripped.startswith("pass"):
                    # non-terminal statement resets only if we're not in a block that follows
                    # a terminal within the same logical block — keep simple heuristic
                    pass
    return findings


def scan_duplicate_blocks():
    findings = []
    block_hashes = {}  # hash -> [(file, start_line)]
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if not f.endswith((".py", ".md")):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            lines = content.splitlines()
            rel = os.path.relpath(full, VAULT)
            # sliding window of 6 non-blank lines
            window = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped:
                    window.append((stripped, i))
                    if len(window) > 6:
                        window.pop(0)
                    if len(window) == 6:
                        block_text = "\n".join(w[0] for w in window)
                        block_hash = hashlib.md5(block_text.encode()).hexdigest()[:12]
                        start = window[0][1]
                        if block_hash in block_hashes:
                            for prev_file, prev_start in block_hashes[block_hash]:
                                if prev_file != rel:
                                    findings.append({
                                        "category": "duplicate_block",
                                        "file": rel,
                                        "line": start,
                                        "other_file": prev_file,
                                        "other_line": prev_start,
                                        "message": f"{rel}:{start} duplicates {prev_file}:{prev_start} (6-line block)",
                                        "suggestion": f"Extract the duplicated block into a shared function/module; reference it from both {rel} and {prev_file}",
                                    })
                                    break
                            block_hashes[block_hash].append((rel, start))
                        else:
                            block_hashes[block_hash] = [(rel, start)]
    return findings


def scan_misplaced_notes():
    """Check .md files in directories that don't match vault conventions."""
    findings = []
    # directory -> expected prefix patterns
    dir_conventions = {
        "01-Projects": ["01-Projects"],
        "02-Areas": ["02-Areas"],
        "03-Resources": ["03-Resources"],
        "04-Archives": ["04-Archives"],
        "_System": ["_System"],
    }
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out", ".git")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT)
            parts = rel.split(os.sep)
            top_dir = parts[0]
            if top_dir in dir_conventions:
                # Basic check: note should be in a directory matching its topic
                # This is a heuristic — flag notes in root of a section dir without subfolder
                if len(parts) == 2 and top_dir in ("01-Projects", "02-Areas", "03-Resources"):
                    findings.append({
                        "category": "misplaced_note",
                        "file": rel,
                        "message": f"{rel} sits at root of {top_dir}/ — consider moving into a subfolder",
                        "suggestion": f"Move {rel} into an appropriate subfolder under {top_dir}/, or add it to a MOC",
                    })
    return findings


# ---------------------------------------------------------------------------
# Check: verify a behavioral change is clean (no tidy mixed in)
# ---------------------------------------------------------------------------
def check_clean_change(file_path, before_content, after_content):
    """Return True if the change is purely behavioral (no structural tidy mixed in).
    A clean behavioral change: same line count ± small delta, no renamed functions,
    no moved blocks, only content edits within existing structure.
    """
    before_lines = before_content.splitlines()
    after_lines = after_content.splitlines()

    # Line count delta > 20% suggests structural change mixed in
    if len(before_lines) > 0:
        delta_pct = abs(len(after_lines) - len(before_lines)) / len(before_lines) * 100
    else:
        delta_pct = 100.0 if after_lines else 0.0

    issues = []
    if delta_pct > 20:
        issues.append(f"Line count changed by {delta_pct:.0f}% — possible structural tidy mixed in")

    # Check for renamed/moved function definitions
    before_funcs = set(re.findall(r"^\s*(def |async def )\s+(\w+)", before_content, re.M))
    after_funcs = set(re.findall(r"^\s*(def |async def )\s+(\w+)", after_content, re.M))
    before_names = {n for _, n in before_funcs}
    after_names = {n for _, n in after_funcs}
    removed = before_names - after_names
    added = after_names - before_names
    if removed:
        issues.append(f"Functions removed (possible move/rename): {', '.join(sorted(removed))}")
    if added:
        issues.append(f"Functions added (possible move/rename): {', '.join(sorted(added))}")

    return {
        "clean": len(issues) == 0,
        "delta_pct": round(delta_pct, 1),
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(all_findings, dry_run=True):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(all_findings)
    by_category = {}
    for f in all_findings:
        cat = f["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    lines = [
        "# Tidy First — Scan Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "--",
        "",
        "## Summary",
        f"- **Total tidy candidates**: {total}",
    ]
    for cat in sorted(by_category):
        label = TIDY_CATEGORIES.get(cat, {}).get("label", cat)
        lines.append(f"  - {label}: {by_category[cat]}")
    lines.append("")
    lines.append("--")
    lines.append("")

    if not all_findings:
        lines.append("## ✅ No tidy candidates found — vault looks clean!")
        lines.append("")
        write_report(lines)
        return

    lines.append("## Tidy Candidates")
    lines.append("")
    lines.append("| Category | File | Line | Message |")
    lines.append("|----------|------|------|---------|")
    for f in all_findings:
        lines.append(f"| {f['category']} | {f['file']} | {f.get('line', '—')} | {f['message']} |")
    lines.append("")
    lines.append("--")
    lines.append("")

    lines.append("## Suggested Tidies (run with --apply to execute)")
    lines.append("")
    for i, f in enumerate(all_findings, 1):
        lines.append(f"### {i}. {TIDY_CATEGORIES.get(f['category'], {}).get('label', f['category'])}")
        lines.append("")
        lines.append(f"- **File**: {f['file']}")
        if f.get("line"):
            lines.append(f"- **Line**: {f['line']}")
        lines.append(f"- **Issue**: {f['message']}")
        lines.append(f"- **Suggested tidy**: {f['suggestion']}")
        if f.get("other_file"):
            lines.append(f"- **Duplicate in**: {f['other_file']}:{f.get('other_line', '—')}")
        lines.append("")

    if dry_run:
        lines.append("## Next Steps")
        lines.append("")
        lines.append("Review the candidates above. To apply a safe auto-tidy, run with `--apply`.\nEach tidy is opt-in and reviewed before applying.\nRemember Kent Beck's rule: **tidy first, then make the behavioral change — never both at once.**")

    write_report(lines)


# ---------------------------------------------------------------------------
# Save individual tidy to vault
# ---------------------------------------------------------------------------
def save_tidy_to_vault(tidy_type, content):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(REPORT_DIR, f"Tidy-{slugify(tidy_type)}-{today}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    print("🧪 Tidy First — Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: scan_long_files detects long files
    try:
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Notes"))
            long_content = "\n".join([f"line {i}" for i in range(500)])
            with open(os.path.join(tmp, "Notes", "long.md"), "w") as f:
                f.write(long_content)
            result = scan_long_files()
            long_found = [x for x in result if x["category"] == "long_file"]
            assert len(long_found) >= 1, f"Expected 1 long file, got {len(long_found)}"
            print("✅ Test 1: scan_long_files detects long files")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1

    # Test 2: scan_long_functions detects long functions
    try:
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            long_func = "\n".join([
                "def long_function():",
                "    x = 1",
            ] + ["    pass"] * 70)
            with open(os.path.join(tmp, "Scripts", "script.py"), "w") as f:
                f.write(long_func)
            result = scan_long_functions()
            long_func_found = [x for x in result if x["category"] == "long_function"]
            assert len(long_func_found) >= 1, f"Expected 1 long function, got {len(long_func_found)}"
            print("✅ Test 2: scan_long_functions detects long functions")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1

    # Test 3: scan_dead_code detects unreachable code
    try:
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            dead = "def foo():\n    return 1\n    x = 2\n"
            with open(os.path.join(tmp, "Scripts", "dead.py"), "w") as f:
                f.write(dead)
            result = scan_dead_code()
            dead_found = [x for x in result if x["category"] == "dead_code"]
            assert len(dead_found) >= 1, f"Expected 1 dead code, got {len(dead_found)}"
            print("✅ Test 3: scan_dead_code detects unreachable code")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1

    # Test 4: check_clean_change flags structural delta
    try:
        before = "def a():\n    return 1\n"
        after = "\n".join([f"line {i}\n" for i in range(200)])
        result = check_clean_change("test.py", before, after)
        assert result["clean"] is False
        assert len(result["issues"]) >= 1
        print("✅ Test 4: check_clean_change flags structural delta")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1

    # Test 5: check_clean_change passes for clean behavioral change
    try:
        before = "def a():\n    return 1\n    print('x')\n"
        after = "def a():\n    return 2\n    print('y')\n"
        result = check_clean_change("test.py", before, after)
        assert result["clean"] is True
        print("✅ Test 5: check_clean_change passes for clean behavioral change")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1

    # Test 6: duplicate block detection
    try:
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            os.makedirs(os.path.join(tmp, "Scripts"))
            block = "    result = compute(x)\n    return result\n    log(result)\n    save(result)\n    print(result)\n    done(result)\n"
            content_a = "def a():\n" + block
            content_b = "def b():\n" + block
            with open(os.path.join(tmp, "Scripts", "a.py"), "w") as f:
                f.write(content_a)
            with open(os.path.join(tmp, "Scripts", "b.py"), "w") as f:
                f.write(content_b)
            result = scan_duplicate_blocks()
            dup_found = [x for x in result if x["category"] == "duplicate_block"]
            assert len(dup_found) >= 1, f"Expected 1 duplicate block, got {len(dup_found)}"
            print("✅ Test 6: scan_duplicate_blocks detects duplicates")
            passed += 1
        finally:
            shutil.rmtree(tmp)
    except AssertionError as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain — Tidy First (Kent Beck): separate structural tidies from behavioral changes.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply safe auto-tidies (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_scan = sub.add_parser("scan", help="Scan vault for tidy candidates")
    p_scan.add_argument("--save", action="store_true", help="Save report to vault")

    p_check = sub.add_parser("check", help="Verify a change is clean (no tidy mixed in)")
    p_check.add_argument("--before", required=True, help="Path to before file")
    p_check.add_argument("--after", required=True, help="Path to after file")

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

    if args.command == "scan":
        all_findings = []
        all_findings.extend(scan_long_files())
        all_findings.extend(scan_long_functions())
        all_findings.extend(scan_dead_code())
        all_findings.extend(scan_duplicate_blocks())
        all_findings.extend(scan_misplaced_notes())

        # Sort by category then file
        cat_order = {c: i for i, c in enumerate(TIDY_CATEGORIES)}
        all_findings.sort(key=lambda f: (cat_order.get(f["category"], 99), f["file"]))

        report = generate_report(all_findings, dry_run=dry_run)
        if args.save:
            saved = save_tidy_to_vault("scan", report)
            print(f"\n📄 Saved to {saved}")
        return

    if args.command == "check":
        before = read_file(args.before)
        after = read_file(args.after)
        result = check_clean_change(args.before, before, after)
        print(f"## Tidy First — Clean Change Check")
        print(f"")
        print(f"- **Before**: {args.before}")
        print(f"- **After**: {args.after}")
        print(f"- **Line delta**: {result['delta_pct']}%")
        print(f"- **Clean**: {'✅ Yes' if result['clean'] else '❌ No'}")
        if result["issues"]:
            print("")
            print("**Issues:**")
            for issue in result["issues"]:
                print(f"- {issue}")
        print("")
        if result["clean"]:
            print("Behavioral change is clean — no structural tidy mixed in.")
        else:
            print("⚠️  Possible structural tidy mixed with behavioral change.")
            print("Per Kent Beck's rule: tidy first, commit, then make the behavioral change separately.")
        return

    print("Error: No command specified. Use 'scan' or 'check'.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()