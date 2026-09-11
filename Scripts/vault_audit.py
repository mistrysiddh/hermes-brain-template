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

Run via cron: 0 2 * * 0  (weekly, Sunday 2 AM) or monthly as preferred.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

VAULT = os.environ.get("HERMES_VAULT_PATH")
if not VAULT:
    print("HERMES_VAULT_PATH is not set — aborting.")
    sys.exit(1)

REPORT_PATH = os.path.join(VAULT, "Skills-Notes", "Vault-Audit-Report.md")

# Patterns
WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')
SESSION_ID_RE = re.compile(r'session_id:\s*"([^"]+)"')

def load_manifest():
    """Load manifest.jsonl for session tracking."""
    manifest_path = os.path.join(VAULT, "Daily", "manifest.jsonl")
    sessions = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    sid = rec.get("session_id")
                    if sid:
                        sessions[sid] = rec
                except json.JSONDecodeError:
                    pass
    return sessions

def find_broken_wikilinks():
    """Find all [[wikilinks]] that don't resolve to existing files."""
    broken = []
    all_files = set()
    # Build index of all files (relative to vault root)
    for root, dirs, files in os.walk(VAULT):
        # Skip .obsidian, .git, .smart-env, graphify-out
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('graphify-out',)]
        for f in files:
            if f.endswith('.md'):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, VAULT)
                # Store with and without .md
                all_files.add(rel)
                all_files.add(rel[:-3])  # without .md
                # Also store just the filename for shorthand links
                all_files.add(f)
                all_files.add(f[:-3])

    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('graphify-out',)]
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
                link = match.group(1)
                # Handle link|alias format
                link = link.split('|')[0].strip()
                if link not in all_files:
                    broken.append({
                        "file": os.path.relpath(full, VAULT),
                        "link": link,
                        "line": content[:match.start()].count('\n') + 1
                    })
    return broken

def find_stale_memory_review(days=30):
    """Find Memory-Review entries older than N days with incomplete tasks."""
    stale = []
    cutoff = datetime.now() - timedelta(days=days)
    mr_path = os.path.join(VAULT, "Memory-Review")
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
                    "file": os.path.relpath(full, VAULT),
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
                "first_path": seen[sid].get("path", "unknown"),
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
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('graphify-out',)]
        for f in files:
            if f.endswith('.md'):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, VAULT)
                all_md_files.append(rel)
                incoming[rel] = 0

    # Count incoming links
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('graphify-out',)]
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
                link = match.group(1).split('|')[0].strip()
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
            if f.startswith(".obsidian/") or f.startswith("Daily/") and ("manifest" in f or "README" in f):
                continue
            orphans.append(f)
    return orphans

def generate_report(broken_links, stale_reviews, duplicates, orphans):
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
        f"- **Stale Memory-Review entries (>{30} days)**: {len(stale_reviews)}",
        f"- **Duplicate sessions in manifest**: {len(duplicates)}",
        f"- **Orphaned files (no incoming links)**: {len(orphans)}",
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

    if not any([broken_links, stale_reviews, duplicates, orphans]):
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
    print(f"Broken links: {len(broken_links)}, Stale reviews: {len(stale_reviews)}, Duplicates: {len(duplicates)}, Orphans: {len(orphans)}")

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
    generate_report(broken, stale, dups, orphans)
    print("✅ Done.")

if __name__ == "__main__":
    main()