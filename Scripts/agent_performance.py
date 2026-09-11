#!/usr/bin/env python3
"""
Hermes Brain — Agent Performance Dashboard Generator.

Analyzes session archives and skill usage to produce a performance
report: Skills-Notes/Agent-Performance.md with Dataview-friendly tables.

Metrics:
- Skill usage frequency (which skills/tools actually get invoked)
- Session volume trends (daily/weekly session counts)
- Average messages per session
- Tool call patterns (what tools are used most)
- Top sessions by token usage (if available)
- Memory-Review throughput (promoted vs. pending)

Run manually or via cron alongside hourly_archive.py / vault_audit.py.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta
from collections import Counter, defaultdict

VAULT = os.environ.get("HERMES_VAULT_PATH")
if not VAULT:
    print("HERMES_VAULT_PATH is not set — aborting.")
    sys.exit(1)

REPORT_PATH = os.path.join(VAULT, "Skills-Notes", "Agent-Performance.md")
DAILY = os.path.join(VAULT, "Daily")
MANIFEST = os.path.join(DAILY, "manifest.jsonl")
SKILL_LINKS = os.path.join(VAULT, "Skills-Notes", "Skill-to-Chat-Links.md")

# Patterns
TOOL_CALL_FENCE = re.compile(r'```json\s*\n(.*?)\n```', re.S)
MESSAGE_COUNT_RE = re.compile(r'message_count:\s*(\d+)')
SESSION_ID_RE = re.compile(r'session_id:\s*"([^"]+)"')
CREATED_RE = re.compile(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})')
TOKEN_USAGE_RE = re.compile(r'prompt_tokens":\s*(\d+).*?"completion_tokens":\s*(\d+)')

def load_manifest():
    """Load manifest for session metadata."""
    sessions = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
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

def scan_daily_sessions():
    """Walk Daily/ and extract metadata from each session file."""
    sessions = []
    if not os.path.exists(DAILY):
        return sessions
    
    for root, _, files in os.walk(DAILY):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            if fname.lower() in ("readme.md", "timeline.md", "chat-correlation.md", "manifest.jsonl"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    head = f.read(3000)
                    content = f.read()
            except Exception:
                continue
            
            # Extract metadata from frontmatter/head
            sid_match = SESSION_ID_RE.search(head)
            msg_match = MESSAGE_COUNT_RE.search(head)
            created_match = CREATED_RE.search(head)
            
            # Try to find tool calls in the full content
            tool_calls = []
            for match in re.finditer(r'```json\s*\n(.*?)\n```', content, re.S):
                try:
                    calls = json.loads(match.group(1))
                    if isinstance(calls, list):
                        for call in calls:
                            if isinstance(call, dict) and call.get("function"):
                                tool_calls.append(call["function"].get("name", "unknown"))
                except:
                    pass
            
            # Token usage from model_config
            prompt_tokens = 0
            completion_tokens = 0
            token_match = re.search(r'prompt_tokens["\s:]+(\d+).*?completion_tokens["\s:]+(\d+)', head)
            if token_match:
                prompt_tokens = int(token_match.group(1))
                completion_tokens = int(token_match.group(2))
            
            sessions.append({
                "file": os.path.relpath(fpath, VAULT),
                "session_id": sid_match.group(1) if sid_match else None,
                "message_count": int(msg_match.group(1)) if msg_match else 0,
                "tool_calls": tool_calls,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "date": created_match.group(0) if created_match else None,
            })
    
    return sessions

def load_skill_links():
    """Parse Skill-to-Chat-Links.md for skill usage."""
    skill_usage = Counter()
    if not os.path.exists(SKILL_LINKS):
        return skill_usage
    try:
        with open(SKILL_LINKS, encoding="utf-8") as f:
            content = f.read()
        # Count skill headings (### SkillName)
        for match in re.finditer(r'^###\s+(.+)$', content, re.M):
            skill = match.group(1).strip()
            # Count links under this skill
            section_start = match.end()
            next_heading = content.find('\n### ', section_start)
            if next_heading == -1:
                next_heading = len(content)
            section = content[section_start:next_heading]
            link_count = len(re.findall(r'\[\[.*?\]\]', section))
            if link_count > 0:
                skill_usage[skill] = link_count
    except Exception:
        pass
    return skill_usage

def compute_daily_stats(sessions):
    """Compute per-day statistics."""
    by_day = defaultdict(lambda: {"sessions": 0, "messages": 0, "tokens": 0})
    for s in sessions:
        if s["date"]:
            # Extract date from created_at
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', s["date"])
            if date_match:
                day = date_match.group(1)
            else:
                day = "unknown"
        else:
            day = "unknown"
        by_day[day]["sessions"] += 1
        by_day[day]["messages"] += s["message_count"]
        by_day[day]["tokens"] += s["total_tokens"]
    return by_day

def compute_tool_usage(sessions):
    """Count tool usage across all sessions."""
    tool_counter = Counter()
    for s in sessions:
        for tool in s["tool_calls"]:
            tool_counter[tool] += 1
    return tool_counter

def generate_report(sessions, skill_usage, daily_stats, tool_usage):
    """Generate Agent-Performance.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_sessions = len(sessions)
    total_messages = sum(s["message_count"] for s in sessions)
    total_tokens = sum(s["total_tokens"] for s in sessions)
    avg_messages = total_messages / total_sessions if total_sessions else 0
    avg_tokens = total_tokens / total_sessions if total_sessions else 0
    
    lines = [
        f"# Agent Performance Dashboard",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        "",
        "---",
        "",
        "## Overview",
        f"- **Total archived sessions**: {total_sessions}",
        f"- **Total messages**: {total_messages:,}",
        f"- **Average messages/session**: {avg_messages:.1f}",
        f"- **Total tokens (tracked)**: {total_tokens:,}",
        f"- **Average tokens/session**: {avg_tokens:,.0f}",
        "",
        "---",
        ""
    ]
    
    # Skill usage
    if skill_usage:
        lines.append("## 🎯 Skill Usage (from Skill-to-Chat-Links)")
        lines.append("")
        lines.append("| Skill | Sessions Invoked |")
        lines.append("|-------|------------------|")
        for skill, count in skill_usage.most_common():
            lines.append(f"| {skill} | {count} |")
        lines.append("")
    else:
        lines.append("## 🎯 Skill Usage")
        lines.append("")
        lines.append("*Run `generate_skill_links.py` to populate skill usage data.*")
        lines.append("")
    
    # Tool usage
    if tool_usage:
        lines.append("## 🔧 Tool Usage Frequency")
        lines.append("")
        lines.append("| Tool | Calls |")
        lines.append("|------|-------|")
        for tool, count in tool_usage.most_common(20):
            lines.append(f"| {tool} | {count} |")
        lines.append("")
    
    # Daily trends (last 14 days)
    lines.append("## 📈 Daily Session Trends (Last 14 Days)")
    lines.append("")
    lines.append("| Date | Sessions | Messages | Tokens |")
    lines.append("|------|----------|----------|--------|")
    sorted_days = sorted(daily_stats.keys())[-14:]
    for day in sorted_days:
        if day == "unknown":
            continue
        stats = daily_stats[day]
        lines.append(f"| {day} | {stats['sessions']} | {stats['messages']} | {stats['tokens']:,} |")
    lines.append("")
    
    # Top sessions by tokens
    token_sessions = sorted([s for s in sessions if s["total_tokens"] > 0], 
                           key=lambda x: x["total_tokens"], reverse=True)[:10]
    if token_sessions:
        lines.append("## 🏆 Top Sessions by Token Usage")
        lines.append("")
        lines.append("| Session | Tokens | Messages | Date |")
        lines.append("|---------|--------|----------|------|")
        for s in token_sessions:
            fname = os.path.basename(s["file"])
            date = s["date"] if s["date"] else "unknown"
            if date != "unknown":
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date)
                date = date_match.group(1) if date_match else date
            lines.append(f"| [[{os.path.relpath(s['file'], VAULT)[:-3]}|{fname}]] | {s['total_tokens']:,} | {s['message_count']} | {date} |")
        lines.append("")
    
    # Memory-Review throughput
    lines.append("## 📋 Memory-Review Throughput")
    lines.append("")
    lines.append("*Run `consolidate_memory.py` to update candidate promotion stats.*")
    lines.append("")
    
    lines.append("---")
    lines.append(f"*Report generated by `Scripts/agent_performance.py` — {now}*")
    
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"Report written to {REPORT_PATH}")

def main():
    print("📊 Generating Agent Performance Dashboard...")
    sessions = scan_daily_sessions()
    print(f"  Scanned {len(sessions)} session files")
    skill_usage = load_skill_links()
    print(f"  Loaded {len(skill_usage)} skills from Skill-to-Chat-Links")
    daily_stats = compute_daily_stats(sessions)
    tool_usage = compute_tool_usage(sessions)
    print(f"  Computed daily stats for {len(daily_stats)} days")
    print(f"  Found {len(tool_usage)} unique tools")
    generate_report(sessions, skill_usage, daily_stats, tool_usage)
    print("✅ Done.")

if __name__ == "__main__":
    main()