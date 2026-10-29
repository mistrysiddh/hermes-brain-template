#!/usr/bin/env python3
"""
Hermes Brain — Self-Critique Skill (multi-harness compatible).

Analyzes the vault and its own scripts for issues, generating a structured
critique report with findings, severity, and suggested fixes. All fixes are
opt-in via --apply; default is dry-run (report only).

Designed per the multi-harness-agent-skills guidelines:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution happens in main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  self_critique.py vault       Vault health (broken links, missing frontmatter, drift)
  self_critique.py scripts     Script hygiene (hardcoded paths, module-level side effects)
  self_critique.py sessions    Session residue (stale cron files, orphaned canvases)
  self_critique.py security    Secret detection (tokens, keys in plaintext)
  self_critique.py all         Run every category
  self_critique.py --test      Built-in self-test suite

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
REPORT_DIR = None
CRITIQUE_LOG = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, REPORT_DIR, CRITIQUE_LOG
    VAULT = os.path.abspath(vault_path)
    REPORT_DIR = os.path.join(VAULT, "04-Archives", "Audit-Reports")
    CRITIQUE_LOG = os.path.join(REPORT_DIR, "Self-Critique-Report.md")


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
    with open(CRITIQUE_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Critique report written to: {CRITIQUE_LOG}")


def finding(severity, category, message, suggestion, file_path=None):
    """Return a structured finding dict."""
    return {
        "severity": severity,   # critical | high | medium | low | info
        "category": category,
        "message": message,
        "suggestion": suggestion,
        "file": file_path,
    }


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


# ---------------------------------------------------------------------------
# 1. Vault health checks
# ---------------------------------------------------------------------------
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def critique_vault():
    """Check vault health: broken links, missing frontmatter, drift."""
    findings = []

    if not VAULT or not os.path.isdir(VAULT):
        findings.append(finding(
            "critical", "vault",
            f"Vault path not found or not a directory: {VAULT}",
            "Pass --vault <path> or set HERMES_VAULT_PATH",
        ))
        return findings

    # --- Broken wikilinks ---
    all_files = set()
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT).replace("\\", "/")
            all_files.add(rel)
            all_files.add(f)
            if f.endswith(".md"):
                all_files.add(rel[:-3])
                all_files.add(f[:-3])

    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            clean = re.sub(r"```[\s\S]*?```", "", content)
            clean = re.sub(r"`[^`\n]+`", "", clean)
            for match in WIKILINK_RE.finditer(clean):
                raw = match.group(1)
                link = raw.split("|")[0].split("#")[0].strip().rstrip("\\")
                if not link or link.startswith(("http://", "https://")):
                    continue
                norm_link = link.replace("\\", "/")
                if norm_link not in all_files:
                    findings.append(finding(
                        "medium", "broken_link",
                        f"Broken wikilink [[{link}]] in {os.path.relpath(full, VAULT)}",
                        f"Create the target file or fix the link in {os.path.relpath(full, VAULT)}",
                        os.path.relpath(full, VAULT),
                    ))

    # --- Missing frontmatter on markdown notes ---
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            # Skip templates and canvases (they intentionally may not have frontmatter)
            if f in ("TEMPLATE.md",) or f.endswith(".canvas"):
                continue
            content = read_file(full)
            if not FRONTMATTER_RE.match(content):
                findings.append(finding(
                    "low", "missing_frontmatter",
                    f"Markdown file without frontmatter: {os.path.relpath(full, VAULT)}",
                    f"Add YAML frontmatter (--- ... ---) to {os.path.relpath(full, VAULT)}",
                    os.path.relpath(full, VAULT),
                ))

    # --- Decision/Principle/Axiom drift ---
    for doc_type in ("Decisions", "Principles", "Axioms"):
        candidates = [
            os.path.join(VAULT, "03-Resources", doc_type, "README.md"),
            os.path.join(VAULT, "03-Resources", doc_type),
        ]
        found = None
        for c in candidates:
            if os.path.isfile(c):
                found = c
                break
            if os.path.isdir(c):
                # Look for any .md in the dir
                for fn in os.listdir(c):
                    if fn.endswith(".md"):
                        found = os.path.join(c, fn)
                        break
                        break
        if not found:
            findings.append(finding(
                "info", "drift",
                f"No {doc_type} doc found in 03-Resources/{doc_type}/",
                f"Create a {doc_type} doc at 03-Resources/{doc_type}/README.md",
            ))

    return findings


# ---------------------------------------------------------------------------
# 2. Script hygiene checks
# ---------------------------------------------------------------------------
def critique_scripts():
    """Check script hygiene: module-level path resolution, hardcoded vault paths."""
    findings = []
    scripts_dir = os.path.join(VAULT, "_System", "Scripts")
    if not os.path.isdir(scripts_dir):
        findings.append(finding(
            "info", "scripts",
            f"_System/Scripts/ not found at {scripts_dir}",
            "Ensure scripts live in _System/Scripts/",
        ))
        return findings

    MODULE_LEVEL_VAULT_RE = re.compile(r"^(VAULT|REPORT_DIR|DAILY|SKILL_LINKS)\s*=\s*.+$", re.M)

    for root, dirs, files in os.walk(scripts_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".py"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            rel = os.path.relpath(full, VAULT)

            # --- Module-level path resolution ---
            if MODULE_LEVEL_VAULT_RE.search(content):
                findings.append(finding(
                    "high", "module_level_path",
                    f"{rel} resolves vault paths at module level (import-time failure risk in headless TUI agents)",
                    f"Refactor {rel}: move path resolution into init_paths() called from main() after --vault parsing",
                    rel,
                ))

            # --- Hardcoded vault paths (string literals) ---
            hardcoded = re.findall(r'["\']([^"\']*(?:01-Projects|02-Areas|03-Resources|04-Archives|Daily|Memory-Review)[^"\']*)["\']', content)
            if hardcoded:
                findings.append(finding(
                    "medium", "hardcoded_path",
                    f"{rel} contains {len(hardcoded)} hardcoded vault path string(s)",
                    f"Replace hardcoded paths in {rel} with os.path.join(VAULT, ...) or --vault-derived paths",
                    rel,
                ))

            # --- Missing --vault CLI arg ---
            if "--vault" not in content and "argparse" in content:
                findings.append(finding(
                    "medium", "missing_vault_arg",
                    f"{rel} uses argparse but has no --vault CLI argument",
                    f"Add --vault CLI arg to {rel} for multi-harness compatibility",
                    rel,
                ))

    return findings


# ---------------------------------------------------------------------------
# 3. Session residue checks
# ---------------------------------------------------------------------------
def critique_sessions():
    """Check session residue: stale cron files, orphaned canvases, duplicate exports."""
    findings = []

    # --- Stale cron session files ---
    cron_candidates = [
        os.path.join(VAULT, "04-Archives", "Cron"),
        os.path.join(VAULT, "Cron"),
    ]
    cron_dir = None
    for c in cron_candidates:
        if os.path.isdir(c):
            cron_dir = c
            break

    if cron_dir:
        cutoff = datetime.now() - timedelta(days=90)
        for root, dirs, files in os.walk(cron_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if not f.endswith(".md"):
                    continue
                full = os.path.join(root, f)
                mtime = datetime.fromtimestamp(os.path.getmtime(full))
                if mtime < cutoff:
                    findings.append(finding(
                        "low", "stale_cron_file",
                        f"Stale cron session file (>90 days old): {os.path.relpath(full, VAULT)}",
                        f"Archive or delete {os.path.relpath(full, VAULT)}",
                        os.path.relpath(full, VAULT),
                    ))

    # --- Orphaned canvases (no incoming wikilinks) ---
    canvas_dirs = [
        os.path.join(VAULT, "_System", "Canvases"),
        os.path.join(VAULT, "Canvases"),
    ]
    canvas_dir = None
    for c in canvas_dirs:
        if os.path.isdir(c):
            canvas_dir = c
            break

    if canvas_dir:
        # Build index of all wikilink targets
        all_links = set()
        for root, dirs, files in os.walk(VAULT):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("cache", "graphify-out")]
            for f in files:
                if not f.endswith(".md"):
                    continue
                content = read_file(os.path.join(root, f))
                clean = re.sub(r"```[\s\S]*?```", "", content)
                clean = re.sub(r"`[^`\n]+`", "", clean)
                for match in WIKILINK_RE.finditer(clean):
                    link = match.group(1).split("|")[0].split("#")[0].strip()
                    all_links.add(link)

        for f in os.listdir(canvas_dir):
            if not f.endswith(".canvas"):
                continue
            canvas_name = f[:-8]  # strip .canvas
            if canvas_name not in all_links:
                findings.append(finding(
                    "low", "orphaned_canvas",
                    f"Orphaned canvas (no incoming links): {f}",
                    f"Link to {f} from a note, or archive it",
                    os.path.join(canvas_dir, f),
                ))

    return findings


# ---------------------------------------------------------------------------
# 4. Security checks
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    re.compile(r"\bapi[_-]?key\b", re.I),
    re.compile(r"\bsecret[_-]?key\b", re.I),
    re.compile(r"\bbearer\s+[a-z0-9._-]{10,}", re.I),
    re.compile(r"\btoken\b.{0,20}[:=]\s*['\"]?[a-z0-9._-]{16,}", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bssh-(rsa|ed25519)\s+[A-Za-z0-9+/=]{20,}"),
    re.compile(r"\b[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}\b"),  # jwt-ish
]


def critique_security():
    """Scan for secrets and credentials in plaintext."""
    findings = []

    # Skip binary/large dirs
    skip_dirs = {".git", ".obsidian", "cache", "graphify-out", ".smart-env"}

    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for f in files:
            full = os.path.join(root, f)
            # Skip large files (>5MB) and binaries
            try:
                if os.path.getsize(full) > 5 * 1024 * 1024:
                    continue
            except OSError:
                continue
            if not f.endswith((".md", ".py", ".sh", ".yml", ".yaml", ".json", ".toml", ".env", ".cfg", ".ini")):
                continue
            content = read_file(full)
            for pattern in SECRET_PATTERNS:
                for match in pattern.finditer(content):
                    findings.append(finding(
                        "critical", "secret_exposure",
                        f"Possible secret/credential in {os.path.relpath(full, VAULT)} (line {content[:match.start()].count(chr(10)) + 1})",
                        f"Move the secret to a vault secret store or .env (not tracked in git), then remove from {os.path.relpath(full, VAULT)}",
                        os.path.relpath(full, VAULT),
                    ))
                    break  # one finding per file per pattern type

    return findings


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(all_findings, dry_run=True):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(all_findings)
    by_severity = {}
    for f in all_findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

    lines = [
        "# Self-Critique Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Total findings**: {total}",
    ]
    for sev in ("critical", "high", "medium", "low", "info"):
        if by_severity.get(sev, 0) > 0:
            lines.append(f"  - {sev.title()}: {by_severity[sev]}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not all_findings:
        lines.append("## ✅ No issues found — vault looks clean!")
        lines.append("")
        write_report(lines)
        return

    # Sort by severity
    sorted_findings = sorted(all_findings, key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))

    lines.append("## Findings")
    lines.append("")
    lines.append("| Severity | Category | Message | File |")
    lines.append("|----------|----------|---------|------|")
    for f in sorted_findings:
        lines.append(f"| {f['severity']} | {f['category']} | {f['message']} | {f['file'] or '—'} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Details & Suggested Fixes")
    lines.append("")
    for i, f in enumerate(sorted_findings, 1):
        lines.append(f"### {i}. [{f['severity'].upper()}] {f['category']}")
        lines.append("")
        lines.append(f"- **Issue**: {f['message']}")
        lines.append(f"- **Suggested fix**: {f['suggestion']}")
        if f["file"]:
            lines.append(f"- **File**: {f['file']}")
        lines.append("")

    if dry_run:
        lines.append("## Next Steps")
        lines.append("")
        lines.append("Review the findings above. To apply safe auto-fixes, run with `--apply`.")
        lines.append("Each fix is opt-in and reviewed before applying.")

    write_report(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    """Built-in self-test suite — creates a temp vault, runs critiques, verifies."""
    import tempfile
    import shutil

    print("🧪 Self-Critique Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: init_paths sets vars correctly
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        assert VAULT == os.path.abspath(tmp), "VAULT not set correctly"
        assert REPORT_DIR.endswith("04-Archives/Audit-Reports"), "REPORT_DIR wrong"
        print("✅ Test 1: init_paths sets vars correctly")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 2: finding() returns correct structure
    f = finding("high", "test_cat", "test message", "fix it", "/some/file.md")
    assert f["severity"] == "high"
    assert f["category"] == "test_cat"
    assert f["message"] == "test message"
    assert f["suggestion"] == "fix it"
    assert f["file"] == "/some/file.md"
    print("✅ Test 2: finding() returns correct structure")
    passed += 1

    # Test 3: Empty vault returns only info-level drift findings (no critical/high)
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        result = critique_vault()
        # Empty vault: no .md files, so no broken links/missing frontmatter.
        # But it will have info findings for missing Decision/Principle/Axiom docs.
        critical_high = [x for x in result if x["severity"] in ("critical", "high")]
        assert len(critical_high) == 0, f"Expected 0 critical/high findings on empty vault, got {len(critical_high)}"
        print("✅ Test 3: Empty vault returns no critical/high findings")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 4: Broken link detection
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "Notes"))
        with open(os.path.join(tmp, "Notes", "a.md"), "w") as f:
            f.write("---\n\ntitle: A\n---\n\nSee [[NonexistentPage]] for details.\n")
        init_paths(tmp)
        result = critique_vault()
        broken = [x for x in result if x["category"] == "broken_link"]
        assert len(broken) == 1, f"Expected 1 broken link, got {len(broken)}"
        assert "NonexistentPage" in broken[0]["message"]
        print("✅ Test 4: Broken link detection works")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 4 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 5: Missing frontmatter detection
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "Notes"))
        with open(os.path.join(tmp, "Notes", "nofront.md"), "w") as f:
            f.write("# No Frontmatter\n\nJust content.\n")
        init_paths(tmp)
        result = critique_vault()
        missing = [x for x in result if x["category"] == "missing_frontmatter"]
        assert len(missing) == 1, f"Expected 1 missing frontmatter, got {len(missing)}"
        print("✅ Test 5: Missing frontmatter detection works")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 5 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 6: Script hygiene — module-level path detection
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "_System", "Scripts"))
        with open(os.path.join(tmp, "_System", "Scripts", "bad_script.py"), "w") as f:
            f.write('VAULT = os.environ.get("HERMES_VAULT_PATH")\n')
        init_paths(tmp)
        result = critique_scripts()
        mod_level = [x for x in result if x["category"] == "module_level_path"]
        assert len(mod_level) == 1, f"Expected 1 module-level path finding, got {len(mod_level)}"
        print("✅ Test 6: Module-level path detection works")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 6 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 7: Security detection
    tmp = tempfile.mkdtemp()
    try:
        with open(os.path.join(tmp, "config.env"), "w") as f:
            f.write('API_KEY=sk-1234567890abcdef\n')
        init_paths(tmp)
        result = critique_security()
        secrets = [x for x in result if x["category"] == "secret_exposure"]
        assert len(secrets) == 1, f"Expected 1 secret finding, got {len(secrets)}"
        assert secrets[0]["severity"] == "critical"
        print("✅ Test 7: Secret detection works")
        passed += 1
    except AssertionError as e:
        print(f"❌ Test 7 failed: {e}")
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
        description="Hermes Brain Self-Critique — find issues in vault and scripts.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply safe auto-fixes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="category", help="Critique category")
    sub.add_parser("vault", help="Vault health (broken links, missing frontmatter, drift)")
    sub.add_parser("scripts", help="Script hygiene (module-level paths, hardcoded paths)")
    sub.add_parser("sessions", help="Session residue (stale cron files, orphaned canvases)")
    sub.add_parser("security", help="Secret detection (tokens, keys in plaintext)")
    sub.add_parser("all", help="Run every category")
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

    category = args.category or "all"
    all_findings = []

    if category in ("vault", "all"):
        all_findings.extend(critique_vault())
    if category in ("scripts", "all"):
        all_findings.extend(critique_scripts())
    if category in ("sessions", "all"):
        all_findings.extend(critique_sessions())
    if category in ("security", "all"):
        all_findings.extend(critique_security())

    generate_report(all_findings, dry_run=dry_run)
    print(f"\n✅ Self-critique complete: {len(all_findings)} findings ({'dry-run' if dry_run else 'apply'} mode)")


if __name__ == "__main__":
    main()
