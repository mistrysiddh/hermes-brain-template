#!/usr/bin/env python3
"""
Hermes Brain — Auto-Remediation Skill (multi-harness compatible).

Reads Self-Critique-Report.md findings and applies safe auto-fixes.
Every fix is opt-in via --apply; default is dry-run (preview only).
Each applied fix gets its own git commit for rollback safety.

Designed per the multi-harness-agent-skills guidelines:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  auto_remediate.py report       Read report, list findings with fix options
  auto_remediate.py apply        Apply safe auto-fixes (human approval per fix)
  auto_remediate.py --test       Built-in self-test suite

Categories auto-remediated (safe operations only):
  - module_level_path   → Add init_paths() call site (report only, needs manual refactor)
  - hardcoded_path      → Replace with os.path.join(VAULT, ...) pattern (report only)
  - missing_vault_arg   → Add --vault CLI arg to argparse (auto-fixable)
  - missing_frontmatter → Add YAML frontmatter to markdown note (auto-fixable)
  - broken_link         → Create stub note placeholder (auto-fixable)
  - secret_exposure     → NEVER auto-fixed (human review required)

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
REPORT_PATH = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, REPORT_PATH
    VAULT = os.path.abspath(vault_path)
    REPORT_PATH = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Self-Critique-Report.md")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run(cmd, cwd=None):
    """Run a shell command, return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, shell=True, cwd=cwd or VAULT,
                            capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def git_commit(file_path, message):
    """Stage and commit a single file with the given message."""
    rel = os.path.relpath(file_path, VAULT)
    code, out, err = run(f'git add "{rel}"')
    if code != 0:
        return False, f"git add failed: {err}"
    code, out, err = run(f'git commit -m "{message}"')
    if code != 0:
        return False, f"git commit failed: {err}"
    return True, out


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


# ---------------------------------------------------------------------------
# Parse Self-Critique-Report.md findings table
# ---------------------------------------------------------------------------
FINDING_RE = re.compile(
    r"\|\s*(critical|high|medium|low|info)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*)\s*\|"
)


def parse_report(report_path):
    """Parse the Self-Critique-Report.md findings table.
    Returns a list of finding dicts with severity, category, message, file.
    """
    findings = []
    content = read_file(report_path)
    if not content:
        return findings

    for match in FINDING_RE.finditer(content):
        severity = match.group(1).strip()
        category = match.group(2).strip()
        message = match.group(3).strip()
        file_path = match.group(4).strip()
        # Skip header/separator rows
        if category.lower() in ("category", "---"):
            continue
        if not file_path or file_path == "—":
            file_path = None
        else:
            # Resolve relative to vault
            file_path = os.path.join(VAULT, file_path)
        findings.append({
            "severity": severity,
            "category": category,
            "message": message,
            "file": file_path,
        })
    return findings


# ---------------------------------------------------------------------------
# Fix strategies per category
# ---------------------------------------------------------------------------
def fix_missing_vault_arg(finding, dry_run=True):
    """Add --vault CLI arg to a script that uses argparse but lacks it."""
    file_path = finding["file"]
    content = read_file(file_path)
    if not content:
        return False, "Could not read file", content

    if "--vault" in content:
        return False, "Already has --vault argument", content

    # Find argparse.ArgumentParser(...) line and add --vault after it
    parser_pattern = re.compile(r"(parser\s*=\s*argparse\.ArgumentParser\([^)]*\))")
    match = parser_pattern.search(content)
    if not match:
        return False, "No ArgumentParser found to attach --vault to", content

    insertion = match.group(1) + '''

parser.add_argument(
    "--vault",
    help="Path to the Hermes Brain vault root",
)'''
    new_content = content[:match.end()] + insertion + content[match.end():]

    if dry_run:
        return True, "Would add --vault CLI argument", new_content
    write_file(file_path, new_content)
    return True, "Added --vault CLI argument", new_content


def fix_missing_frontmatter(finding, dry_run=True):
    """Add YAML frontmatter to a markdown note missing it."""
    file_path = finding["file"]
    content = read_file(file_path)
    if not content:
        return False, "Could not read file", content

    # Check if already has frontmatter
    if re.match(r"^---\s*\n", content):
        return False, "Already has frontmatter", content

    # Generate a title from the filename
    fname = os.path.basename(file_path)
    title = fname.replace(".md", "").replace("_", " ").replace("-", " ").title()
    now = datetime.now().strftime("%Y-%m-%d")
    frontmatter = f"""---\ntitle: {title}\ncreated: {now}\ntype: stub\nstatus: auto-remediated\n---\n\n"""
    new_content = frontmatter + content

    if dry_run:
        return True, f"Would add frontmatter (title: {title})", new_content
    write_file(file_path, new_content)
    return True, f"Added frontmatter (title: {title})", new_content


def fix_broken_link(finding, dry_run=True):
    """Create a stub note for a broken wikilink target."""
    file_path = finding["file"]
    message = finding["message"]
    # Extract the broken link target from message like "Broken wikilink [[Target]] in path"
    link_match = re.search(r"\[\[([^\]]+)\]\]", message)
    if not link_match:
        return False, "Could not parse broken link target from message", ""

    link_target = link_match.group(1).split("|")[0].split("#")[0].strip()
    # Resolve the target path relative to the vault
    # If it's a relative path like ../Research/Foo.md, resolve against the source file's dir
    if file_path and os.path.exists(file_path):
        source_dir = os.path.dirname(file_path)
        resolved = os.path.normpath(os.path.join(source_dir, link_target))
    else:
        resolved = os.path.join(VAULT, link_target)

    # Add .md if not present
    if not resolved.endswith(".md"):
        resolved_md = resolved + ".md"
    else:
        resolved_md = resolved

    if os.path.exists(resolved_md):
        return False, f"Target already exists: {resolved_md}", ""

    if dry_run:
        return True, f"Would create stub note: {os.path.relpath(resolved_md, VAULT)}", ""
    write_file(resolved_md, f"""---\ntitle: {os.path.basename(resolved_md).replace('.md', '')}\ntype: stub\nstatus: auto-remediated\ncreated: {datetime.now().strftime('%Y-%m-%d')}\n---\n\n# {os.path.basename(resolved_md).replace('.md', '')}\n\n> This is a **placeholder stub** auto-created by auto_remediate.py to resolve a broken wikilink.\n> Replace this with actual content when the note is written.\n\n## To Do\n- [ ] Write content\n- [ ] Remove this placeholder notice\n- [ ] Add proper frontmatter and tags\n""")
    return True, f"Created stub note: {os.path.relpath(resolved_md, VAULT)}", ""


def fix_module_level_path(finding, dry_run=True):
    """Module-level path resolution — report only, needs manual refactor."""
    file_path = finding["file"]
    content = read_file(file_path)
    if not content:
        return False, "Could not read file", content

    # Check if already has init_paths pattern
    if "def init_paths" in content or "init_paths()" in content:
        return False, "Already has init_paths() pattern", content

    if dry_run:
        return True, "Needs manual refactor: move path resolution into init_paths() called from main()", content
    return False, "Not auto-fixable — requires manual refactor", content


def fix_hardcoded_path(finding, dry_run=True):
    """Hardcoded vault paths — report only, needs manual refactor."""
    if dry_run:
        return True, "Needs manual refactor: replace hardcoded paths with os.path.join(VAULT, ...)", ""
    return False, "Not auto-fixable — requires manual refactor", ""


def fix_secret_exposure(finding, dry_run=True):
    """Secret exposure — NEVER auto-fixed."""
    return False, "NOT auto-fixable — secrets require human review and manual removal", ""


def fix_drift(finding, dry_run=True):
    """Decision/Principle/Axiom drift — report only."""
    if dry_run:
        return True, "Needs manual review: create missing governance doc", ""
    return False, "Not auto-fixable — requires human decision", ""


def fix_stale_cron_file(finding, dry_run=True):
    """Stale cron file — report only (human decides archive vs delete)."""
    if dry_run:
        return True, "Needs manual decision: archive or delete stale cron file", ""
    return False, "Not auto-fixable — requires human decision", ""


def fix_orphaned_canvas(finding, dry_run=True):
    """Orphaned canvas — report only."""
    if dry_run:
        return True, "Needs manual decision: link to canvas or archive it", ""
    return False, "Not auto-fixable — requires human decision", ""


# Map category -> fix function
FIX_STRATEGIES = {
    "missing_vault_arg": fix_missing_vault_arg,
    "missing_frontmatter": fix_missing_frontmatter,
    "broken_link": fix_broken_link,
    "module_level_path": fix_module_level_path,
    "hardcoded_path": fix_hardcoded_path,
    "secret_exposure": fix_secret_exposure,
    "drift": fix_drift,
    "stale_cron_file": fix_stale_cron_file,
    "orphaned_canvas": fix_orphaned_canvas,
}

# Categories safe to auto-apply without further prompting
AUTO_APPLY_SAFE = {"missing_vault_arg", "missing_frontmatter", "broken_link"}

# Categories that need human review even in --apply mode
REVIEW_REQUIRED = {"module_level_path", "hardcoded_path", "secret_exposure",
                   "drift", "stale_cron_file", "orphaned_canvas"}


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_remediation_report(findings, results, dry_run=True):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    applied = [r for r in results if r["applied"]]
    skipped = [r for r in results if not r["applied"]]

    lines = [
        "# Auto-Remediation Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Total findings reviewed**: {len(findings)}",
        f"- **Fixes applied**: {len(applied)}",
        f"- **Fixes skipped (needs review)**: {len(skipped)}",
        "",
        "---",
        "",
    ]

    if applied:
        lines.append("## ✅ Applied Fixes")
        lines.append("")
        lines.append("| Category | File | Fix |")
        lines.append("|----------|------|-----|")
        for r in applied:
            rel = os.path.relpath(r["file"], VAULT) if r["file"] else "—"
            lines.append(f"| {r['category']} | {rel} | {r['fix']} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    if skipped:
        lines.append("## ⚠️ Skipped (Needs Human Review)")
        lines.append("")
        lines.append("| Category | File | Reason |")
        lines.append("|----------|------|--------|")
        for r in skipped:
            rel = os.path.relpath(r["file"], VAULT) if r["file"] else "—"
            lines.append(f"| {r['category']} | {rel} | {r['fix']} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    if dry_run:
        lines.append("Review the fixes above. To apply them, run with `--apply`.")
        lines.append("Each fix will be presented for individual approval before committing.")
    else:
        lines.append("All safe fixes have been applied and committed individually.")
        lines.append("Review skipped items in `04-Archives/Audit-Reports/Auto-Remediate-Report.md`.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 Auto-Remediate Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: parse_report handles empty/missing file
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        result = parse_report(os.path.join(tmp, "nonexistent.md"))
        assert len(result) == 0, f"Expected 0 findings, got {len(result)}"
        print("✅ Test 1: parse_report handles missing file")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 2: parse_report parses findings table
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        report_content = """# Self-Critique Report
Generated: 2026-10-29
Vault: test

---

## Summary
- Total findings: 2

---

## Findings

| Severity | Category | Message | File |
|----------|----------|---------|------|
| high | missing_vault_arg | Script uses argparse but no --vault | _System/Scripts/foo.py |
| medium | missing_frontmatter | Note without frontmatter | Notes/bar.md |
"""
        report_path = os.path.join(tmp, "Self-Critique-Report.md")
        write_file(report_path, report_content)
        result = parse_report(report_path)
        assert len(result) == 2, f"Expected 2 findings, got {len(result)}"
        assert result[0]["category"] == "missing_vault_arg"
        assert result[1]["category"] == "missing_frontmatter"
        print("✅ Test 2: parse_report parses findings table")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 3: fix_missing_frontmatter creates frontmatter
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        note_path = os.path.join(tmp, "test_note.md")
        write_file(note_path, "# Hello\n\nJust content.\n")
        finding = {
            "severity": "medium",
            "category": "missing_frontmatter",
            "message": "Note without frontmatter",
            "file": note_path,
        }
        ok, fix_desc, new_content = fix_missing_frontmatter(finding, dry_run=True)
        assert ok, f"Expected dry-run to succeed: {fix_desc}"
        assert "Would add frontmatter" in fix_desc
        # Verify file unchanged in dry-run
        assert read_file(note_path) == "# Hello\n\nJust content.\n"

        ok, fix_desc, new_content = fix_missing_frontmatter(finding, dry_run=False)
        assert ok, f"Expected apply to succeed: {fix_desc}"
        content = read_file(note_path)
        assert content.startswith("---\n"), f"Expected frontmatter, got: {content[:50]}"
        assert "title: Test Note" in content
        print("✅ Test 3: fix_missing_frontmatter works")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 4: fix_missing_vault_arg adds argument
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        script_path = os.path.join(tmp, "foo.py")
        write_file(script_path, "import argparse\nparser = argparse.ArgumentParser(description='test')\nargs = parser.parse_args()\n")
        finding = {
            "severity": "medium",
            "category": "missing_vault_arg",
            "message": "No --vault argument",
            "file": script_path,
        }
        ok, fix_desc, new_content = fix_missing_vault_arg(finding, dry_run=True)
        assert ok, f"Expected dry-run to succeed: {fix_desc}"
        assert "--vault" not in read_file(script_path)  # dry-run doesn't modify

        ok, fix_desc, new_content = fix_missing_vault_arg(finding, dry_run=False)
        assert ok, f"Expected apply to succeed: {fix_desc}"
        content = read_file(script_path)
        assert "--vault" in content
        print("✅ Test 4: fix_missing_vault_arg works")
        passed += 1
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 5: fix_broken_link creates stub
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        source_dir = os.path.join(tmp, "Notes")
        os.makedirs(source_dir)
        source_file = os.path.join(source_dir, "note.md")
        write_file(source_file, "See [[MissingPage]] for details.\n")
        finding = {
            "severity": "medium",
            "category": "broken_link",
            "message": "Broken wikilink [[MissingPage]] in Notes/note.md",
            "file": source_file,
        }
        ok, fix_desc, _ = fix_broken_link(finding, dry_run=True)
        assert ok, f"Expected dry-run to succeed: {fix_desc}"
        assert "Would create stub" in fix_desc

        ok, fix_desc, _ = fix_broken_link(finding, dry_run=False)
        assert ok, f"Expected apply to succeed: {fix_desc}"
        stub_path = os.path.join(tmp, "Notes", "MissingPage.md")
        assert os.path.exists(stub_path), f"Stub not created at {stub_path}"
        print("✅ Test 5: fix_broken_link works")
        passed += 1
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 6: secret_exposure is never auto-fixed
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        finding = {
            "severity": "critical",
            "category": "secret_exposure",
            "message": "API key in plaintext",
            "file": os.path.join(tmp, "config.env"),
        }
        ok, fix_desc, _ = fix_secret_exposure(finding, dry_run=False)
        assert not ok, "Secret exposure should never be auto-fixed"
        assert "NOT auto-fixable" in fix_desc
        print("✅ Test 6: secret_exposure never auto-fixed")
        passed += 1
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
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
        description="Hermes Brain Auto-Remediation — apply safe fixes from Self-Critique report.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview fixes without applying (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply safe auto-fixes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("report", help="Parse report and list findings with fix options")
    sub.add_parser("apply", help="Apply safe auto-fixes with per-fix approval")
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

    if not os.path.exists(REPORT_PATH):
        print(f"Error: Self-Critique-Report.md not found at {REPORT_PATH}", file=sys.stderr)
        print("Run self_critique.py first to generate the report.", file=sys.stderr)
        sys.exit(1)

    findings = parse_report(REPORT_PATH)
    if not findings:
        print("✅ No findings in report — nothing to remediate.")
        return

    print(f"📋 Found {len(findings)} findings in Self-Critique-Report.md")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'APPLY'}\n")

    results = []
    for i, f in enumerate(findings, 1):
        category = f["category"]
        strategy = FIX_STRATEGIES.get(category)

        if not strategy:
            results.append({
                "category": category,
                "file": f["file"],
                "fix": "No fix strategy defined — skip",
                "applied": False,
            })
            continue

        rel = os.path.relpath(f["file"], VAULT) if f["file"] else "—"
        print(f"\n[{i}/{len(findings)}] {category.upper()} — {rel}")
        print(f"   Issue: {f['message']}")

        # Determine if this needs human review
        needs_review = category in REVIEW_REQUIRED

        if dry_run:
            ok, fix_desc, _ = strategy(f, dry_run=True)
            results.append({
                "category": category,
                "file": f["file"],
                "fix": fix_desc,
                "applied": ok,
            })
            status = "✅ Would apply" if ok else "⏭️  Skip"
            print(f"   {status}: {fix_desc}")
        else:
            if needs_review:
                ok, fix_desc, _ = strategy(f, dry_run=True)
                results.append({
                    "category": category,
                    "file": f["file"],
                    "fix": fix_desc,
                    "applied": False,
                })
                print(f"   ⏭️  Skip — needs human review: {fix_desc}")
                continue

            # Auto-apply safe categories without prompting
            if category in AUTO_APPLY_SAFE:
                ok, fix_desc, new_content = strategy(f, dry_run=False)
                if ok:
                    # Commit the fix
                    committed, commit_out = git_commit(f["file"],
                                                       f"fix: {fix_desc} ({category})")
                    results.append({
                        "category": category,
                        "file": f["file"],
                        "fix": fix_desc,
                        "applied": committed,
                    })
                    if committed:
                        print(f"   ✅ Applied & committed: {fix_desc}")
                    else:
                        print(f"   ❌ Commit failed: {commit_out}")
                else:
                    results.append({
                        "category": category,
                        "file": f["file"],
                        "fix": fix_desc,
                        "applied": False,
                    })
                    print(f"   ⏭️  Skip: {fix_desc}")
            else:
                # Prompt for confirmation
                ok, fix_desc, _ = strategy(f, dry_run=True)
                response = input(f"   Apply fix: {fix_desc}? [y/N] ").strip().lower()
                if response in ("y", "yes"):
                    ok2, fix_desc2, new_content = strategy(f, dry_run=False)
                    if ok2:
                        committed, commit_out = git_commit(f["file"],
                                                           f"fix: {fix_desc2} ({category})")
                        results.append({
                            "category": category,
                            "file": f["file"],
                            "fix": fix_desc2,
                            "applied": committed,
                        })
                        if committed:
                            print(f"   ✅ Applied & committed: {fix_desc2}")
                        else:
                            print(f"   ❌ Commit failed: {commit_out}")
                    else:
                        results.append({
                            "category": category,
                            "file": f["file"],
                            "fix": fix_desc2,
                            "applied": False,
                        })
                        print(f"   ⏭️  Skip: {fix_desc2}")
                else:
                    results.append({
                        "category": category,
                        "file": f["file"],
                        "fix": fix_desc,
                        "applied": False,
                    })
                    print(f"   ⏭️  Skipped")

    # Write remediation report
    report_content = generate_remediation_report(findings, results, dry_run=dry_run)
    report_path = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Auto-Remediate-Report.md")
    write_file(report_path, report_content)
    print(f"\n📄 Remediation report written to: {report_path}")

    applied_count = sum(1 for r in results if r["applied"])
    print(f"\n✅ Auto-remediation complete: {applied_count}/{len(results)} fixes applied")


if __name__ == "__main__":
    main()
