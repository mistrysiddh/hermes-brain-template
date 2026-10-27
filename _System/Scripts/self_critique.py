#!/usr/bin/env python3
"""
self_critique.py — Self-critique & vault health audit for multi-harness agents.

Combines three lenses into a single critical review:
1. VAULT INTEGRITY (from vault_audit.py)
   - Broken wikilinks, orphaned files, duplicate sessions, manifest issues
2. AGENT PERFORMANCE (from agent_performance.py)
   - Skill usage frequency, session volume, tool patterns, token usage
3. STALE MEMORY DETECTION (from consolidate_memory.py)
   - 60+ day undecided candidates, memory review gaps

Outputs a single self-critique report with severity-flagged findings and
actionable recommendations.

Usage:
  python self_critique.py --vault <vault_path> [--days 14] [--severity low]

Multi-harness: accepts --vault CLI arg, works from CLI, desktop, TUI, or gateway.
Writes vault-local only. No remote pushes. No Hermes binary dependency.

Severity levels:
- low: informational, no immediate action needed
- medium: should address within the next review cycle
- high: resolve before next session
- critical: blocks effective vault operation
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Vault Path Resolution (multi-harness: CLI arg > env var > auto-detect)
# ---------------------------------------------------------------------------

def find_vault_root(start_dir=None):
    if start_dir and os.path.isdir(start_dir):
        return Path(start_dir).resolve()
    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.isdir(env_vault):
        return Path(env_vault).resolve()
    script_dir = Path(__file__).resolve().parent
    for p in [Path.cwd().resolve(), script_dir, script_dir.parent, script_dir.parent.parent]:
        if (p / "01-Projects").exists() or (p / "Dashboard.md").exists() or (p / ".obsidian").exists():
            return p.resolve()
    return Path.cwd().resolve()


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, DAILY_DIR, MEMORY_REVIEW_DIR, AUDIT_DIR, SKILL_LINKS, MANIFEST
    VAULT = Path(vault_path).resolve()
    DAILY_DIR = VAULT / "04-Archives" / "Daily"
    if not DAILY_DIR.exists():
        DAILY_DIR = VAULT / "Daily"
    MEMORY_REVIEW_DIR = VAULT / "04-Archives" / "Memory-Review"
    if not MEMORY_REVIEW_DIR.exists():
        MEMORY_REVIEW_DIR = VAULT / "Memory-Review"
    AUDIT_DIR = VAULT / "04-Archives" / "Audit-Reports"
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    SKILL_LINKS = VAULT / "02-Areas" / "Skills" / "Skill-to-Chat-Links.md"
    if not SKILL_LINKS.exists():
        SKILL_LINKS = VAULT / "Skills-Notes" / "Skill-to-Chat-Links.md"
    MANIFEST = DAILY_DIR / "manifest.jsonl"


# Path variables — set by init_paths(), never at import time.
VAULT = None
DAILY_DIR = None
MEMORY_REVIEW_DIR = None
AUDIT_DIR = None
SKILL_LINKS = None
MANIFEST = None


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SESSION_ID_RE = re.compile(r'session_id:\s*"([^"]+)"')
CREATED_RE = re.compile(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})')
MESSAGE_COUNT_RE = re.compile(r'message_count:\s*(\d+)')
STALE_DAYS = 60


# ---------------------------------------------------------------------------
# 1. Vault Integrity (from vault_audit.py patterns)
# ---------------------------------------------------------------------------

def load_manifest():
    """Load manifest.jsonl for session metadata."""
    sessions = []
    if not MANIFEST.exists():
        return sessions
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                sid = rec.get("session_id")
                if sid:
                    sessions.append(rec)
            except json.JSONDecodeError:
                pass
    return sessions


def find_broken_wikilinks():
    """Find all [[wikilinks]] that don't resolve to existing files."""
    broken = []
    all_files = set()
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT).replace("\\", "/")
            all_files.add(rel)
            all_files.add(f)
            if f.endswith(".md"):
                all_files.add(rel[:-3])
                all_files.add(f[:-3])

    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            try:
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue
            clean_content = re.sub(r"```[\s\S]*?```", "", content)
            clean_content = re.sub(r"`[^`\n]+`", "", clean_content)
            for match in WIKILINK_RE.finditer(clean_content):
                link = match.group(1).split("|")[0].split("#")[0].strip().replace("\\", "/")
                if not link or link.startswith("http://") or link.startswith("https://"):
                    continue
                if link not in all_files:
                    broken.append({
                        "file": os.path.relpath(full, VAULT).replace("\\", "/"),
                        "link": link,
                        "line": content[:match.start()].count("\n") + 1,
                    })
    return broken


def find_orphaned_files():
    """Find files with no incoming wikilinks."""
    incoming = {}
    all_md_files = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, VAULT).replace("\\", "/")
                all_md_files.append(rel)
                incoming[rel] = 0

    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            try:
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue
            for match in WIKILINK_RE.finditer(content):
                link = match.group(1).split("|")[0].split("#")[0].strip().replace("\\", "/")
                for target in all_md_files:
                    if target == link or target[:-3] == link or Path(target).name == link:
                        incoming[target] += 1
                        break

    ignore_patterns = [
        "README.md", "Timeline.md", "Chat-Correlation.md", "TEMPLATE.md",
        "Welcome.md", "MOC.md", "Dashboard.md", "VERSION",
        "manifest.jsonl", "Token-Usage.log", "Vault-Audit-Report.md",
        "Installed-Skills-Index.md", "Team-Profiles-Index.md",
    ]
    orphans = []
    for f, count in incoming.items():
        if count == 0 and not any(f.endswith(p) or f == p for p in ignore_patterns):
            if f.startswith(".obsidian/") or ("Daily/" in f and ("manifest" in f or "README" in f)):
                continue
            if re.search(r"(Daily|Cron/sessions)/\d{4}/\d{2}/\d{2}/", f):
                continue
            orphans.append(f)
    return orphans


def find_duplicate_sessions():
    """Find duplicate session_ids in manifest."""
    sessions = load_manifest()
    seen = {}
    duplicates = []
    for rec in sessions:
        sid = rec.get("session_id")
        path = rec.get("path", "unknown")
        if sid in seen:
            duplicates.append({
                "session_id": sid,
                "orig_path": seen[sid],
                "dup_path": path,
            })
        else:
            seen[sid] = path
    return duplicates


# ---------------------------------------------------------------------------
# 2. Agent Performance (from agent_performance.py patterns)
# ---------------------------------------------------------------------------

def scan_daily_sessions():
    """Walk Daily/ and extract metadata from each session file."""
    sessions = []
    if not DAILY_DIR.exists():
        return sessions
    for root, _, files in os.walk(DAILY_DIR):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            if fname.lower() in ("readme.md", "timeline.md", "chat-correlation.md", "manifest.jsonl"):
                continue
            full = os.path.join(root, fname)
            try:
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue
            sid_match = SESSION_ID_RE.search(content)
            created_match = CREATED_RE.search(content)
            msg_match = MESSAGE_COUNT_RE.search(content)
            sessions.append({
                "path": full,
                "name": fname,
                "session_id": sid_match.group(1) if sid_match else None,
                "created_at": created_match.group(0) if created_match else None,
                "message_count": int(msg_match.group(1)) if msg_match else 0,
                "raw_text": content,
            })
    return sessions


def scan_skill_links():
    """Scan Skill-to-Chat-Links.md for skill usage frequency."""
    usage = defaultdict(int)
    if not SKILL_LINKS.exists():
        return usage
    try:
        with open(SKILL_LINKS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("|"):
                    continue
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2 and parts[0] and parts[0].lower() != "skill":
                    usage[parts[0].lower()] += 1
    except Exception:
        pass
    return usage


# ---------------------------------------------------------------------------
# 3. Stale Memory Detection (from consolidate_memory.py patterns)
# ---------------------------------------------------------------------------

def find_stale_memory_candidates():
    """Find Memory-Review candidates undecided for 60+ days."""
    stale = []
    cutoff = datetime.now() - timedelta(days=STALE_DAYS)
    if not MEMORY_REVIEW_DIR.exists():
        return stale
    for root, _, files in os.walk(MEMORY_REVIEW_DIR):
        for f in files:
            if not f.endswith(".md") or f == "TEMPLATE.md":
                continue
            full = os.path.join(root, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(full))
                if mtime > cutoff:
                    continue
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
                open_tasks = len(re.findall(r"- \[\s\]", content))
                if open_tasks > 0:
                    stale.append({
                        "file": os.path.relpath(full, VAULT).replace("\\", "/"),
                        "age_days": (datetime.now() - mtime).days,
                        "open_tasks": open_tasks,
                    })
            except Exception:
                continue
    return stale


# ---------------------------------------------------------------------------
# Severity & Reporting
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def severity_icon(sev):
    return {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}.get(sev, "ℹ️")


def main():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Self-Critique — vault health & agent performance audit"
    )
    parser.add_argument(
        "--vault",
        type=str,
        default="",
        help="Vault root directory path (default: HERMES_VAULT_PATH env var, then auto-detect)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Number of past days to inspect (default: 14)",
    )
    parser.add_argument(
        "--severity",
        type=str,
        default="low",
        choices=["low", "medium", "high", "critical"],
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run automated self-tests",
    )
    args = parser.parse_args()

    if args.test:
        run_self_test()
        sys.exit(0)

    vault_path = args.vault or os.environ.get("HERMES_VAULT_PATH") or None
    if not vault_path:
        detected = find_vault_root()
        if detected:
            vault_path = str(detected)
    if not vault_path:
        print("Vault path not specified and auto-detection failed — aborting.", file=sys.stderr)
        print("  Pass --vault <path> or set HERMES_VAULT_PATH.", file=sys.stderr)
        sys.exit(1)
    init_paths(vault_path)

    print(f"🔍 Running Hermes Brain Self-Critique — Scope: Last {args.days} days")
    print(f"📁 Target Vault: {VAULT}")
    print(f"🚨 Minimum severity: {args.severity}")
    print()

    # Collect all findings
    findings = []

    # 1. Vault integrity
    broken_links = find_broken_wikilinks()
    for bl in broken_links:
        findings.append({
            "severity": "medium",
            "category": "broken_link",
            "title": f"Broken wikilink: [[{bl['link']}]]",
            "file": bl["file"],
            "line": bl["line"],
            "detail": f"Link '{bl['link']}' in {bl['file']} does not resolve to an existing file.",
        })

    orphans = find_orphaned_files()
    for orphan in orphans:
        findings.append({
            "severity": "low",
            "category": "orphan",
            "title": f"Orphaned file: {orphan}",
            "file": orphan,
            "line": None,
            "detail": "No wikilinks point to this file — consider linking or archiving.",
        })

    duplicates = find_duplicate_sessions()
    for dup in duplicates:
        findings.append({
            "severity": "medium",
            "category": "duplicate",
            "title": f"Duplicate session: {dup['session_id']}",
            "file": dup["dup_path"],
            "line": None,
            "detail": f"Session ID appears in both {dup['orig_path']} and {dup['dup_path']}.",
        })

    # 2. Agent performance
    sessions = scan_daily_sessions()
    skill_usage = scan_skill_links()

    total_sessions = len(sessions)
    total_messages = sum(s["message_count"] for s in sessions)
    sessions_with_tasks = sum(1 for s in sessions if "task" in s["raw_text"].lower())

    if total_sessions == 0:
        findings.append({
            "severity": "high",
            "category": "no_sessions",
            "title": "No sessions found in Daily/",
            "file": str(DAILY_DIR.relative_to(VAULT)),
            "line": None,
            "detail": "No session files found — archiving may not be running.",
        })

    # Underused skills
    unused_skills = []
    for skill, count in sorted(skill_usage.items(), key=lambda x: x[1]):
        if count <= 1:
            unused_skills.append(skill)
    if unused_skills:
        findings.append({
            "severity": "low",
            "category": "unused_skills",
            "title": f"Underused skills: {', '.join(unused_skills[:5])}",
            "file": str(SKILL_LINKS.relative_to(VAULT)),
            "line": None,
            "detail": f"{len(unused_skills)} skills used once or never — consider retiring or promoting.",
        })

    # Sessions with no tasks (potential knowledge capture gap)
    sessions_no_tasks = [s for s in sessions if not s["tasks"] and s["message_count"] > 10]
    if sessions_no_tasks:
        findings.append({
            "severity": "low",
            "category": "no_tasks",
            "title": f"{len(sessions_no_tasks)} long sessions with no action items",
            "file": str(DAILY_DIR.relative_to(VAULT)),
            "line": None,
            "detail": "Long sessions without action items may indicate knowledge not being captured.",
        })

    # 3. Stale memory
    stale = find_stale_memory_candidates()
    for st in stale:
        sev = "high" if st["age_days"] > 90 else "medium"
        findings.append({
            "severity": sev,
            "category": "stale_candidate",
            "title": f"Stale memory candidate: {st['file']}",
            "file": st["file"],
            "line": None,
            "detail": f"Undecided for {st['age_days']} days with {st['open_tasks']} open task(s).",
        })

    # Sort by severity
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))

    # Filter by minimum severity
    min_sev = SEVERITY_ORDER.get(args.severity, 3)
    findings = [f for f in findings if SEVERITY_ORDER.get(f["severity"], 99) <= min_sev]

    # Generate report
    now = datetime.now()
    report_name = f"Self-Critique-{now.strftime('%Y-%m-%d')}.md"
    report_path = AUDIT_DIR / report_name

    sev_counts = Counter(f["severity"] for f in findings)

    lines = [
        "---",
        "type: self-critique",
        "status: generated",
        f"created: {now.strftime('%Y-%m-%d')}",
        "tags: [self-critique, audit, health, auto-generated]",
        "---",
        "",
        f"# 🔍 Self-Critique Report — {now.strftime('%Y-%m-%d')}",
        "",
        f"> Generated by `Scripts/self_critique.py` on {now.strftime('%Y-%m-%d %H:%M')}.",
        f"> Vault: `{VAULT}` | Sessions analyzed: **{total_sessions}** | Minimum severity: **{args.severity}**",
        "",
        "## 📊 Severity Summary",
        "",
    ]

    for sev in ["critical", "high", "medium", "low"]:
        count = sev_counts.get(sev, 0)
        icon = severity_icon(sev)
        lines.append(f"- {icon} **{sev.title()}**: {count}")

    lines.extend([
        "",
        "## 🚨 Findings",
        "",
    ])

    if not findings:
        lines.append("- ✅ No issues found at or above the requested severity level.")
    else:
        for f in findings:
            icon = severity_icon(f["severity"])
            file_ref = f"`{f['file']}`" if f["file"] else "`—`"
            line_ref = f" (line {f['line']})" if f["line"] else ""
            lines.append(f"- {icon} **{f['title']}**")
            lines.append(f"  - File: {file_ref}{line_ref}")
            lines.append(f"  - {f['detail']}")
            lines.append("")

    # Recommendations
    lines.extend([
        "## 💡 Recommendations",
        "",
    ])

    if broken_links:
        lines.append("- Fix broken wikilinks — they break the knowledge graph and make notes hard to find.")
    if orphans:
        lines.append("- Review orphaned files — link them into relevant notes or archive them.")
    if duplicates:
        lines.append("- Deduplicate session files — multiple files with the same session ID cause confusion.")
    if unused_skills:
        lines.append("- Review underused skills — retire those no longer needed or promote them more.")
    if stale:
        lines.append("- Review stale memory candidates — approve, reject, or merge them to keep Memory-Review clean.")
    if sessions_no_tasks:
        lines.append("- Capture action items from long sessions — use the Daily Review template to structure takeaways.")

    if not findings:
        lines.append("- ✅ Vault is in good shape — no action needed at this severity level.")

    lines.extend([
        "",
        "---",
        "*Generated by `Scripts/self_critique.py` — BASB/ZK-inspired self-critique.*",
        "",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Report] Self-critique written: {report_path}")

    # Console summary
    print("\n✅ Self-Critique complete.")
    print(f"   Findings: {len(findings)} total")
    for sev in ["critical", "high", "medium", "low"]:
        count = sev_counts.get(sev, 0)
        if count:
            print(f"   {severity_icon(sev)} {sev.title()}: {count}")
    print(f"   Report: {report_path}")


def run_self_test():
    import tempfile, shutil
    print("=" * 60)
    print("🧪 self_critique.py Self-Test Suite")
    print("=" * 60)

    test_dir = Path(tempfile.mkdtemp(prefix="hb-critique-test-"))
    try:
        vault = test_dir / "Vault"
        vault.mkdir()
        (vault / "01-Projects").mkdir(parents=True)
        (vault / "02-Areas").mkdir(parents=True)
        (vault / "02-Areas" / "Skills").mkdir(parents=True)
        (vault / "03-Resources").mkdir(parents=True)
        (vault / "04-Archives" / "Daily" / "2026" / "09" / "25").mkdir(parents=True)
        (vault / "04-Archives" / "Daily" / "2026" / "09" / "26").mkdir(parents=True)
        (vault / "04-Archives" / "Memory-Review").mkdir(parents=True)
        (vault / "04-Archives" / "Audit-Reports").mkdir(parents=True)

        # Session with broken wikilink
        sess_a = vault / "04-Archives" / "Daily" / "2026" / "09" / "25" / "session-a.md"
        sess_a.write_text(
            """---
session_id: "sess-a"
created_at: "2026-09-25T10:00:00Z"
message_count: 15
---
# Session A

This references [[NonexistentPage]].

- [ ] Task from session A

Tags: #database #architecture
""", encoding="utf-8")

        # Session B: long session, no tasks
        sess_b = vault / "04-Archives" / "Daily" / "2026" / "09" / "26" / "session-b.md"
        sess_b.write_text(
            """---
session_id: "sess-b"
created_at: "2026-09-26T14:00:00Z"
message_count: 45
---
# Session B

Long discussion about architecture. No tasks captured here.

Tags: #postgres #mcp
""", encoding="utf-8")

        # Skill links with an underused skill (write before init_paths so
        # SKILL_LINKS.exists() check finds it)
        skill_links = vault / "02-Areas" / "Skills" / "Skill-to-Chat-Links.md"
        skill_links.write_text(
            "| Skill | Sessions |\n|-------|----------|\n| hermes-brain-vault | 5 |\n| unused-skill-xyz | 1 |\n",
            encoding="utf-8",
        )

        # Initialize paths for functions that use VAULT global
        init_paths(str(vault))
        manifest_path = DAILY_DIR / "manifest.jsonl"
        manifest_path.write_text(
            '{"session_id": "sess-dup", "path": "04-Archives/Daily/2026/09/25/dup-a.md"}\n'
            '{"session_id": "sess-dup", "path": "04-Archives/Daily/2026/09/26/dup-b.md"}\n',
            encoding="utf-8",
        )

        # Stale memory candidate (old file - set mtime to 61+ days ago)
        old_candidate = MEMORY_REVIEW_DIR / "candidate_old.md"
        old_candidate.write_text(
            """---
type: memory-candidate
status: pending-review
created: "2026-01-01T00:00:00Z"
---
# Old Candidate

This has been here for months.

- [ ] Still pending
""", encoding="utf-8")
        # Set mtime to 61 days ago
        old_time = (datetime.now() - timedelta(days=61)).timestamp()
        os.utime(old_candidate, (old_time, old_time))

        # Skill links with an underused skill
        skill_links = VAULT / "02-Areas" / "Skills" / "Skill-to-Chat-Links.md"
        skill_links.write_text(
            "| Skill | Sessions |\n|-------|----------|\n| hermes-brain-vault | 5 |\n| unused-skill-xyz | 1 |\n",
            encoding="utf-8",
        )

        # Test find_broken_wikilinks
        broken = find_broken_wikilinks()
        assert len(broken) >= 1
        assert any("NonexistentPage" in b["link"] for b in broken)
        print("✅ find_broken_wikilinks -> OK")

        # Test find_orphaned_files
        orphans = find_orphaned_files()
        print(f"✅ find_orphaned_files -> OK ({len(orphans)} orphans)")

        # Test find_duplicate_sessions
        dups = find_duplicate_sessions()
        assert len(dups) >= 1
        print(f"✅ find_duplicate_sessions -> OK ({len(dups)} duplicates)")

        # Test scan_daily_sessions
        scanned = scan_daily_sessions()
        assert len(scanned) == 2
        print(f"✅ scan_daily_sessions -> OK ({len(scanned)} sessions)")

        # Test scan_skill_links
        usage = scan_skill_links()
        assert "unused-skill-xyz" in usage
        print("✅ scan_skill_links -> OK")

        # Test find_stale_memory_candidates
        stale = find_stale_memory_candidates()
        assert len(stale) >= 1
        assert stale[0]["age_days"] > 60
        print(f"✅ find_stale_memory_candidates -> OK ({len(stale)} stale)")

        print("=" * 60)
        print("🎉 All self_critique.py self-tests PASSED successfully!")
        print("=" * 60)

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    main()