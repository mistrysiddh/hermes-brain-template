#!/usr/bin/env python3
"""
Hermes Brain — Vault Integrity Checker.

Scans the vault for common issues and generates a report in
Skills-Notes/Vault-Audit-Report.md. Designed to run via cron (weekly/monthly).

Checks:
- Broken internal links (Obsidian-style [[wikilinks]])
- Stale Memory-Review entries (>30 days old)
- Duplicate session exports (same session_id in manifest)
- Missing/empty daily session files
- Orphaned files (no incoming links)
- Manifest consistency (missing files, incomplete entries)

Run via cron: 0 2 * * 0  (weekly, Sunday 2 AM) or monthly as preferred.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

def get_vault():
    for arg in sys.argv[1:]:
        if not arg.startswith("--") and os.path.isdir(arg):
            return os.path.abspath(arg)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if os.path.exists(os.path.join(cand, ".obsidian")) or os.path.exists(os.path.join(cand, "01-Projects")):
        return cand
    cand = os.path.abspath(os.path.join(script_dir, ".."))
    if os.path.exists(os.path.join(cand, ".obsidian")) or os.path.exists(os.path.join(cand, "01-Projects")):
        return cand
    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.exists(env_vault):
        return env_vault
    return None

VAULT = get_vault()
if not VAULT:
    print("Could not resolve vault path — set HERMES_VAULT_PATH or pass vault directory as argument.")
    sys.exit(1)

rep_cand = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Vault-Audit-Report.md")
REPORT_PATH = rep_cand if os.path.exists(os.path.dirname(rep_cand)) else os.path.join(VAULT, "Skills-Notes", "Vault-Audit-Report.md")

# Patterns
WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')
SESSION_ID_RE = re.compile(r'session_id:\s*"([^"]+)"')


def load_manifest():
    """Load manifest.jsonl for session tracking."""
    m_cand = os.path.join(VAULT, "04-Archives", "Daily", "manifest.jsonl")
    manifest_path = m_cand if os.path.exists(m_cand) else os.path.join(VAULT, "Daily", "manifest.jsonl")
    sessions = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sid = rec.get("session_id")
                if sid:
                    sessions[sid] = rec
    return sessions


def validate_manifest():
    """Validate manifest.jsonl for consistency and completeness."""
    issues = []
    manifest_path = os.path.join(VAULT, "Daily", "manifest.jsonl")
    if not os.path.exists(manifest_path):
        issues.append({"type": "missing", "message": "manifest.jsonl does not exist"})
        return issues

    sessions = load_manifest()

    # Check for missing files referenced in manifest
    for sid, rec in sessions.items():
        path = rec.get("path", "")
        if path and not os.path.exists(os.path.join(VAULT, path)):
            issues.append({
                "type": "missing_file",
                "session_id": sid,
                "path": path,
                "message": f"Manifest references non-existent file: {path}"
            })

    # Check for session_ids without required fields
    for sid, rec in sessions.items():
        if not rec.get("title"):
            issues.append({
                "type": "incomplete",
                "session_id": sid,
                "message": f"Session {sid} missing title"
            })
        if not rec.get("exported_at"):
            issues.append({
                "type": "incomplete",
                "session_id": sid,
                "message": f"Session {sid} missing exported_at timestamp"
            })

    return issues


def find_broken_wikilinks():
    """Find all [[wikilinks]] that don't resolve to existing files."""
    broken = []
    all_files = set()
    # Build index of all files (relative to vault root)
    for root, dirs, files in os.walk(VAULT):
        # Skip .obsidian, .git, .smart-env, cache, graphify-out
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('cache', 'graphify-out')]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT).replace('\\', '/')
            all_files.add(rel)
            all_files.add(f)
            if f.endswith('.md'):
                all_files.add(rel[:-3])
                all_files.add(f[:-3])

    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('cache', 'graphify-out')]
        for f in files:
            if not f.endswith('.md'):
                continue
            full = os.path.join(root, f)
            try:
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue
            # Strip code blocks and inline code to avoid false positives on code examples/comments
            clean_content = re.sub(r'```[\s\S]*?```', '', content)
            clean_content = re.sub(r'`[^`\n]+`', '', clean_content)
            for match in WIKILINK_RE.finditer(clean_content):
                raw_link = match.group(1)
                link = raw_link.replace(r'\|', '|').replace(r'\]', ']').split('|')[0].split('#')[0].strip().rstrip('\\')
                if not link or link.startswith("http://") or link.startswith("https://"):
                    continue
                norm_link = link.replace('\\', '/')
                if norm_link not in all_files:
                    broken.append({
                        "file": os.path.relpath(full, VAULT).replace('\\', '/'),
                        "link": link,
                        "line": content[:match.start()].count('\n') + 1
                    })
    return broken


def find_stale_memory_review(days=30):
    """Find Memory-Review entries older than N days with incomplete tasks."""
    stale = []
    cutoff = datetime.now() - timedelta(days=days)
    mr_cand = os.path.join(VAULT, "04-Archives", "Memory-Review")
    mr_path = mr_cand if os.path.exists(mr_cand) else os.path.join(VAULT, "Memory-Review")
    if not os.path.exists(mr_path):
        return stale
    for root, dirs, files in os.walk(mr_path):
        for f in files:
            if not f.endswith('.md') or f == "TEMPLATE.md":
                continue
            full = os.path.join(root, f)
            try:
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue
            # Check file mtime
            mtime = datetime.fromtimestamp(os.path.getmtime(full))
            if mtime > cutoff:
                continue
            # Check for incomplete tasks
            open_tasks = len(re.findall(r'- \[ \]', content))
            if open_tasks > 0:
                stale.append({
                    "file": os.path.relpath(full, VAULT).replace('\\', '/'),
                    "age_days": (datetime.now() - mtime).days,
                    "open_tasks": open_tasks
                })
    return stale


def find_duplicate_sessions():
    """Find duplicate session_ids in manifest."""
    sessions = load_manifest()
    duplicates = []
    seen = {}
    for sid, rec in sessions.items():
        if sid in seen:
            duplicates.append({
                "session_id": sid,
                "orig_path": seen[sid].get("path", "unknown"),
                "dup_path": rec.get("path", "unknown")
            })
        else:
            seen[sid] = rec
    return duplicates


def find_orphaned_files():
    """Find files with no incoming wikilinks (excluding known scaffolding)."""
    # Build reverse index
    incoming = {}
    all_md_files = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('cache', 'graphify-out')]
        for f in files:
            if f.endswith('.md'):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, VAULT).replace('\\', '/')
                all_md_files.append(rel)
                incoming[rel] = 0

    # Count incoming links
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('cache', 'graphify-out')]
        for f in files:
            if not f.endswith('.md'):
                continue
            full = os.path.join(root, f)
            try:
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue
            for match in WIKILINK_RE.finditer(content):
                link = match.group(1).split('|')[0].split('#')[0].strip().replace('\\', '/')
                # Try to resolve to a known file
                for target in all_md_files:
                    if target == link or target[:-3] == link or os.path.basename(target) == link or os.path.basename(target[:-3]) == link:
                        incoming[target] += 1
                        break

    # Scaffolding files we don't care about
    ignore_patterns = [
        "README.md", "Timeline.md", "Chat-Correlation.md", "TEMPLATE.md",
        "Welcome.md", "MOC.md", "Dashboard.md", "VERSION",
        "manifest.jsonl", "Token-Usage.log", "Vault-Audit-Report.md",
        "Installed-Skills-Index.md", "Team-Profiles-Index.md",
        "Skill-to-Chat-Links.md", "Dataview-Query-Library.md",
    ]

    orphans = []
    for f, count in incoming.items():
        if count == 0 and not any(f.endswith(p) or f == p for p in ignore_patterns):
            # Also ignore files in .obsidian, Daily/ manifest, etc.
            if f.startswith(".obsidian/") or ("Daily/" in f and ("manifest" in f or "README" in f)):
                continue
            orphans.append(f)
    return orphans


def generate_report(broken_links, stale_reviews, duplicates, orphans, manifest_issues):
    """Generate markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Vault Audit Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        "",
        "---",
        "",
        f"## Summary",
        f"- **Broken wikilinks**: {len(broken_links)}",
        f"- **Stale Memory-Review entries (>30 days)**: {len(stale_reviews)}",
        f"- **Duplicate sessions in manifest**: {len(duplicates)}",
        f"- **Orphaned files (no incoming links)**: {len(orphans)}",
        f"- **Manifest issues**: {len(manifest_issues)}",
        "",
        "---",
        ""
    ]

    if broken_links:
        lines.append("## ⚠️ Broken Wikilinks")
        lines.append("")
        lines.append("| File | Broken Link | Line |")
        lines.append("|------|-------------|------|")
        for item in broken_links[:50]:  # cap at 50
            lines.append(f"| {item['file']} | `[[{item['link']}]]` | {item['line']} |")
        if len(broken_links) > 50:
            lines.append(f"\n... and {len(broken_links) - 50} more.")
        lines.append("")

    if stale_reviews:
        lines.append("## 📋 Stale Memory-Review Entries (>30 days, incomplete)")
        lines.append("")
        lines.append("| File | Age (days) | Open Tasks |")
        lines.append("|------|------------|------------|")
        for item in stale_reviews:
            lines.append(f"| {item['file']} | {item['age_days']} | {item['open_tasks']} |")
        lines.append("")

    if duplicates:
        lines.append("## 🔁 Duplicate Sessions in Manifest")
        lines.append("")
        lines.append("| Session ID | First Path | Duplicate Path |")
        lines.append("|------------|------------|----------------|")
        for item in duplicates:
            lines.append(f"| {item['session_id']} | {item['first_path']} | {item['dup_path']} |")
        lines.append("")

    if orphans:
        lines.append("## 🏝️ Orphaned Files (no incoming wikilinks)")
        lines.append("")
        lines.append("*Consider linking these from relevant notes, or they may be safe to archive/delete.*")
        lines.append("")
        for f in orphans[:50]:
            lines.append(f"- {f}")
        if len(orphans) > 50:
            lines.append(f"\n... and {len(orphans) - 50} more.")
        lines.append("")

    if manifest_issues:
        lines.append("## 📋 Manifest Consistency Issues")
        lines.append("")
        lines.append("| Type | Session ID | Details |")
        lines.append("|------|------------|---------|")
        for issue in manifest_issues[:50]:
            sid = issue.get('session_id', 'N/A')
            msg = issue.get('message', str(issue))
            lines.append(f"| {issue['type']} | {sid} | {msg} |")
        if len(manifest_issues) > 50:
            lines.append(f"\n... and {len(manifest_issues) - 50} more.")
        lines.append("")

    if not any([broken_links, stale_reviews, duplicates, orphans, manifest_issues]):
        lines.append("## ✅ All Clean!")
        lines.append("")
        lines.append("No issues detected. Your vault is in excellent shape.")

    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by `Scripts/vault_audit.py` — runs automatically via cron.*")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {REPORT_PATH}")
    print(f"Broken links: {len(broken_links)}, Stale reviews: {len(stale_reviews)}, Duplicates: {len(duplicates)}, Orphans: {len(orphans)}, Manifest issues: {len(manifest_issues)}")


def main():
    print("🔍 Starting vault integrity check...")
    broken = find_broken_wikilinks()
    print(f"  Broken wikilinks: {len(broken)}")
    stale = find_stale_memory_review(30)
    print(f"  Stale reviews: {len(stale)}")
    dups = find_duplicate_sessions()
    print(f"  Duplicate sessions: {len(dups)}")
    orphans = find_orphaned_files()
    print(f"  Orphaned files: {len(orphans)}")
    manifest_issues = validate_manifest()
    print(f"  Manifest issues: {len(manifest_issues)}")
    generate_report(broken, stale, dups, orphans, manifest_issues)
    print("✅ Done.")


if __name__ == "__main__":
    main()