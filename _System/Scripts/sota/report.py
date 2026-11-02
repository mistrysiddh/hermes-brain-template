#!/usr/bin/env python3
"""
Hermes Brain — SOTA Sub-Skill: report (sota/report.py)

Generates the SOTA scan report and persists artifacts:
  - generate_scan_report — markdown report with standing, matrix, gap list
  - save_sota_artifacts — persists last-scan.json and rubric to .sota/
  - CLI orchestrates profile → comparators → matrix → report

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Usage:
  python sota/report.py --vault <path> scan --domain agent-brain-vault
  python sota/report.py --vault <path> scan --domain agent-brain-vault --apply --save
  python sota/report.py --vault <path> --test
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
SOTA_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT, SOTA_DIR
    VAULT = os.path.abspath(vault_path)
    SOTA_DIR = os.path.join(VAULT, ".sota")


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


# Ensure sibling sub-skill modules are importable when run standalone
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_SCRIPT_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

# ---------------------------------------------------------------------------
# Imports from sibling sub-skills
# ---------------------------------------------------------------------------
from sota.profile import build_us_profile as _build_us_profile   # noqa: E402
from sota.comparators import fetch_comparators as _fetch_comparators  # noqa: E402
from sota.comparators import classify_cluster as _classify_cluster  # noqa: E402
from sota.matrix import build_capability_matrix as _build_capability_matrix  # noqa: E402
from sota.matrix import rank_gaps as _rank_gaps  # noqa: E402


# ---------------------------------------------------------------------------
# generate_scan_report — markdown report for SOTA scan
# ---------------------------------------------------------------------------
def generate_scan_report(us_profile, comparators, clusters, us_label, matrix, gaps, dry_run=True):
    """Generate markdown report for SOTA scan."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_skills = sum(1 for m in matrix if m["us"] == "✅")
    total_missing = sum(1 for m in matrix if m["us"] == "❌")
    coverage_pct = round(total_skills / len(matrix) * 100, 1) if matrix else 0

    ts_gaps = len(gaps["table_stakes"])
    if ts_gaps == 0:
        tier = "TOP-TIER"
    elif ts_gaps <= 2:
        tier = "SOLID"
    elif ts_gaps <= 5:
        tier = "BEHIND"
    else:
        tier = "LAGGING"

    lines = [
        "# SOTA Scan Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## 🧭 SOTA Standing",
        f"- **Verdict**: {tier}",
        f"- **Score**: {coverage_pct}% ({total_skills}/{len(matrix)} capabilities)",
        f"- **Standing**: {'AHEAD' if ts_gaps == 0 else 'BEHIND' if ts_gaps > 5 else 'SOLID'} vs {len(comparators)} comparators",
        f"- **Clusters found**: {len(clusters)}",
        f"- **Our cluster**: {us_label}",
        "",
        "---",
        "",
        "## 📊 Capability Matrix",
        "| Capability | Us | SOTA | Gap? | Reference |",
        "|------------|----|------|------|-----------|",
    ]

    for m in matrix:
        lines.append(
            f"| {m['capability']} | {m['us']} | {m['sota']} | {m['gap']} | {m['reference']} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📋 Ranked Gap List")

    if gaps["table_stakes"]:
        lines.append("### Table-Stakes Gaps (do these first)")
        for i, g in enumerate(gaps["table_stakes"], 1):
            lines.append(f"{i}. **{g['capability']}** — {g['tier']} · gap: high")
            lines.append(f"   Study: {g['sota']}")
            lines.append(f"   Step 1: Implement {g['capability']} following Hermes multi-harness pattern")
            lines.append("")

    if gaps["edge"]:
        lines.append("### Edge Gaps (nice-to-have)")
        for i, g in enumerate(gaps["edge"], 1):
            lines.append(f"{i}. **{g['capability']}** — {g['tier']} · gap: medium")
            lines.append(f"   Study: {g['sota']}")
            lines.append("")

    if not gaps["table_stakes"] and not gaps["edge"]:
        lines.append("✅ No gaps — you're at parity with the field!")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📈 Comparators Scanned")
    lines.append("| Repo | Stars | Pushed | Type |")
    lines.append("|------|-------|--------|------|")
    for c in comparators[:10]:
        lines.append(f"| {c['name']} | {c['stars']} | {c['pushed'][:10] if c['pushed'] else 'unknown'} | general |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 💾 Persistence")
    lines.append(f"- Results saved to: `.sota/last-scan.json`")
    lines.append(f"- Rubric saved to: `.sota/rubric.{us_label}.json`")
    lines.append("- Re-run to track progress over time")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. Review table-stakes gaps first — these are the highest priority")
    lines.append("2. For each gap, implement following Hermes multi-harness skill pattern")
    lines.append("3. Re-run `sota_scan.py scan --apply` to track improvement")
    lines.append("")
    lines.append("## SOTA Scan Principle")
    lines.append("- Every gap is tied to a real comparator repo")
    lines.append("- No vague advice — every gap names a real project")
    lines.append("- Scores are reproducible: same rubric, same axis")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# save_sota_artifacts — persist SOTA scan artifacts to vault
# ---------------------------------------------------------------------------
def save_sota_artifacts(matrix, gaps, us_profile, comparators, dry_run=True):
    """Persist SOTA scan artifacts to vault."""
    now = datetime.datetime.now().strftime("%Y-%m-%d")

    last_scan = {
        "date": now,
        "vault": VAULT,
        "matrix": matrix,
        "coverage": {
            "met": sum(1 for m in matrix if m["us"] == "✅"),
            "total": len(matrix),
        },
        "gaps_total": gaps["total"],
        "comparators": comparators[:10],
    }

    rubric = {
        "domain": "agent-brain-vault",
        "version": 1,
        "capabilities": matrix,
    }

    if not dry_run:
        write_file(os.path.join(SOTA_DIR, "last-scan.json"), json.dumps(last_scan, indent=2))
        write_file(os.path.join(SOTA_DIR, f"rubric.agent-brain-vault.json"), json.dumps(rubric, indent=2))

    return last_scan, rubric


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 sota/report.py Self-Test Suite")
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

    # Test 1: generate_scan_report renders correctly
    def test_report():
        matrix = [
            {"id": "a", "capability": "Multi-harness", "us": "✅", "sota": "—",
             "reference": "—", "tier": "table-stakes", "gap": "—"},
            {"id": "b", "capability": "Vault Audit", "us": "❌", "sota": "user/self-critique",
             "reference": "user/self-critique", "tier": "edge", "gap": "edge"},
        ]
        gaps = {"table_stakes": [], "edge": [matrix[1]], "total": 1}
        us_profile = {"domains": ["agent-brain-vault"], "capabilities": [], "total_notes": 1}
        comparators = [{"name": "user/self-critique", "stars": 100, "pushed": "2026-01-01",
                        "url": "https://github.com/user/self-critique", "archived": False}]
        clusters = {"agent-brain-vault": comparators}
        report = generate_scan_report(us_profile, comparators, clusters, "agent-brain-vault",
                                      matrix, gaps, dry_run=True)
        assert "# SOTA Scan Report" in report
        assert "## 🧭 SOTA Standing" in report
        assert "## 📊 Capability Matrix" in report
        assert "## 📋 Ranked Gap List" in report
    check("generate_scan_report renders correctly", test_report)

    # Test 2: save_sota_artifacts writes files in apply mode
    def test_save_artifacts_apply():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            matrix = [{"id": "a", "capability": "A", "us": "✅", "sota": "—",
                       "reference": "—", "tier": "table-stakes", "gap": "—"}]
            gaps = {"table_stakes": [], "edge": [], "total": 0}
            us_profile = {"domains": ["agent-brain-vault"], "capabilities": [], "total_notes": 1}
            comparators = []
            last_scan, rubric = save_sota_artifacts(matrix, gaps, us_profile, comparators, dry_run=False)
            assert os.path.exists(os.path.join(SOTA_DIR, "last-scan.json"))
            assert os.path.exists(os.path.join(SOTA_DIR, "rubric.agent-brain-vault.json"))
            assert last_scan["coverage"]["met"] == 1
        finally:
            shutil.rmtree(tmp)
    check("save_sota_artifacts writes files in apply mode", test_save_artifacts_apply)

    # Test 3: save_sota_artifacts dry-run does not write
    def test_save_artifacts_dryrun():
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            matrix = []
            gaps = {"table_stakes": [], "edge": [], "total": 0}
            us_profile = {"domains": [], "capabilities": [], "total_notes": 0}
            comparators = []
            save_sota_artifacts(matrix, gaps, us_profile, comparators, dry_run=True)
            assert not os.path.exists(SOTA_DIR)
        finally:
            shutil.rmtree(tmp)
    check("save_sota_artifacts dry-run does not write", test_save_artifacts_dryrun)

    # Test 4: generate_scan_report empty gaps
    def test_report_no_gaps():
        matrix = [{"id": "a", "capability": "A", "us": "✅", "sota": "—",
                   "reference": "—", "tier": "table-stakes", "gap": "—"}]
        gaps = {"table_stakes": [], "edge": [], "total": 0}
        us_profile = {"domains": [], "capabilities": [], "total_notes": 0}
        comparators = []
        clusters = {}
        report = generate_scan_report(us_profile, comparators, clusters, "general",
                                      matrix, gaps, dry_run=True)
        assert "✅ No gaps — you're at parity with the field!" in report
    check("generate_scan_report empty gaps", test_report_no_gaps)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain SOTA — report sub-skill.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_scan = sub.add_parser("scan", help="Scan repo against SOTA (dry-run report)")
    p_scan.add_argument("--domain", default="agent-brain-vault", help="Domain to benchmark against")
    p_scan.add_argument("--count", type=int, default=8, help="Max comparators to fetch")

    parser.add_argument("--save", action="store_true", help="Save scan artifacts to vault")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="Write artifacts to vault (overrides --dry-run)")
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

    if args.command != "scan":
        print("Error: No command specified. Use 'scan'.", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Scanning vault against SOTA (domain: {args.domain})...\n")

    # Build our profile
    us_profile = _build_us_profile(VAULT)
    print(f"📋 Profiled vault: {us_profile['total_notes']} notes, "
          f"{len(us_profile['domains'])} domains, {len(us_profile['capabilities'])} capabilities")

    # Fetch comparators
    print(f"🌐 Fetching comparators for domain '{args.domain}'...")
    comparators = _fetch_comparators(args.domain, count=args.count)
    print(f"📡 Found {len(comparators)} comparators")

    # Classify into clusters
    clusters, us_label = _classify_cluster(comparators, us_profile)
    print(f"🎯 Classified into cluster: {us_label} ({len(clusters)} clusters found)")

    # Build matrix
    matrix = _build_capability_matrix(us_profile, comparators, clusters, us_label)
    gaps = _rank_gaps(matrix)

    # Generate report
    report = generate_scan_report(us_profile, comparators, clusters, us_label, matrix, gaps, dry_run=dry_run)
    print(report)

    # Save artifacts
    if not dry_run and args.save:
        last_scan, rubric = save_sota_artifacts(matrix, gaps, us_profile, comparators, dry_run=False)
        print(f"\n📄 Saved scan to: {os.path.join(SOTA_DIR, 'last-scan.json')}")
        print(f"📄 Saved rubric to: {os.path.join(SOTA_DIR, f'rubric.{us_label}.json')}")
    elif dry_run:
        print(f"\n📄 Run with --apply --save to persist scan artifacts to {SOTA_DIR}/")


if __name__ == "__main__":
    main()
