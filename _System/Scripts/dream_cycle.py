#!/usr/bin/env python3
"""
dream_cycle.py — Autonomous Cognitive Reflection & Latent Cross-Linker.

Consolidates recent episodic memories (Daily/ sessions) into semantic knowledge:
1. Scans recent daily sessions (default: last 7-14 days).
2. Discovers latent cross-session associations and topic clusters.
3. Extracts open action items and technical patterns.
4. Produces a Weekly Cognitive Synthesis report: Research/Weekly-Synthesis-YYYY-Www.md.
5. Optionally inserts bilateral Obsidian wikilinks between related sessions (--link).

Usage:
    python Scripts/dream_cycle.py [vault_path] [--days 7] [--link]
"""

import os
import sys
import re
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict, Counter

def find_vault_root(start_dir=None):
    current = Path(start_dir or os.getcwd()).resolve()
    for p in [current, current.parent, current.parent.parent]:
        if (p / "User-Profile.md").exists() or (p / "Dashboard.md").exists():
            return p
    return current

def extract_session_data(file_path):
    """Parse session note for tags, title, topics, and tasks."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # Skip manifest, README, Timeline, etc.
    if file_path.name in ["README.md", "Timeline.md", "Chat-Correlation.md", "manifest.jsonl"]:
        return None

    # Extract tags
    tags = set(re.findall(r"(?:^tags:\s*\[(.*?)\]|#([a-zA-Z0-9_\-]+))", text, re.M))
    flat_tags = set()
    for t_tuple in tags:
        for t in t_tuple:
            if t:
                for item in t.split(","):
                    clean = item.strip().replace("#", "")
                    if clean and clean.lower() not in ["daily", "session", "chat"]:
                        flat_tags.add(clean.lower())

    # Extract tasks
    tasks = []
    for line in text.splitlines():
        m = re.match(r"^\s*-\s+\[ \]\s+(.*?)$", line)
        if m:
            tasks.append(m.group(1).strip())

    # Extract key vocabulary / technical terms
    words = re.findall(r"\b[A-Za-z0-9_-]{4,25}\b", text.lower())
    stopwords = {"this", "that", "with", "from", "have", "here", "were", "what", "when", "your", "user", "assistant", "message", "session", "model", "hermes"}
    vocab = [w for w in words if w not in stopwords and not w.isdigit()]

    return {
        "path": file_path,
        "name": file_path.stem,
        "rel_path": file_path.as_posix(),
        "tags": flat_tags,
        "tasks": tasks,
        "vocab_counts": Counter(vocab)
    }

def calculate_similarity(sess_a, sess_b):
    """Compute lightweight Jaccard similarity across tags and technical vocabulary."""
    # Tag similarity
    common_tags = sess_a["tags"] & sess_b["tags"]
    tag_score = len(common_tags) * 3.0

    # Vocabulary overlap
    top_a = set(w for w, _ in sess_a["vocab_counts"].most_common(30))
    top_b = set(w for w, _ in sess_b["vocab_counts"].most_common(30))
    common_words = top_a & top_b
    word_score = len(common_words) * 0.5

    return tag_score + word_score, common_tags, common_words

def main():
    parser = argparse.ArgumentParser(description="Hermes Brain Dream Cycle & Latent Synthesis")
    parser.add_argument("vault", nargs="?", default=None, help="Vault root directory")
    parser.add_argument("--days", type=int, default=14, help="Number of past days to inspect (default: 14)")
    parser.add_argument("--link", action="store_true", help="Auto-inject Related Sessions backlinks into session notes")
    args = parser.parse_args()

    daily_cand = vault_root / "04-Archives" / "Daily"
    daily_dir = daily_cand if daily_cand.exists() else vault_root / "Daily"
    if not daily_dir.exists():
        print("❌ Daily/ directory not found — nothing to analyze.")
        return

    print(f"🌙 Running Hermes Brain Dream Cycle — Scope: Last {args.days} days")
    
    # 1. Collect recent session notes
    cutoff = datetime.now() - timedelta(days=args.days)
    recent_sessions = []
    
    for f in daily_dir.rglob("*.md"):
        # Match folder date pattern Daily/YYYY/MM/DD
        m = re.search(r"Daily[/\\](\d{4})[/\\](\d{2})[/\\](\d{2})", str(f))
        if m:
            try:
                s_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                if s_date >= cutoff:
                    data = extract_session_data(f)
                    if data:
                        data["date"] = s_date.strftime("%Y-%m-%d")
                        recent_sessions.append(data)
            except ValueError:
                continue

    print(f"  Scanned {len(recent_sessions)} session files within {args.days}-day window.")
    if len(recent_sessions) < 2:
        print("  Not enough sessions to discover cross-session latent patterns.")
        return

    # 2. Discover latent cross-session pairs
    correlations = []
    for i in range(len(recent_sessions)):
        for j in range(i + 1, len(recent_sessions)):
            a = recent_sessions[i]
            b = recent_sessions[j]
            score, shared_tags, shared_words = calculate_similarity(a, b)
            if score >= 4.0:
                correlations.append({
                    "a": a,
                    "b": b,
                    "score": score,
                    "shared_tags": shared_tags,
                    "shared_words": list(shared_words)[:5]
                })

    correlations.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Discovered {len(correlations)} latent cross-session connections.")

    # 3. Generate Weekly Synthesis Report
    now = datetime.now()
    year, week, _ = now.isocalendar()
    report_name = f"Weekly-Synthesis-{year}-W{week:02d}.md"
    res_cand = vault_root / "03-Resources" / "Research"
    res_dir = res_cand if res_cand.exists() else vault_root / "Research"
    report_path = res_dir / report_name
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "---",
        "type: research",
        "status: generated",
        f"created: {now.strftime('%Y-%m-%d')}",
        f"tags: [dream-cycle, synthesis, weekly, review]",
        "---",
        "",
        f"# 🌙 Hermes Brain Cognitive Synthesis — {year} Week {week:02d}",
        "",
        f"> **Generated:** {now.strftime('%Y-%m-%d %H:%M')} | **Window:** Last {args.days} days | **Sessions Analyzed:** {len(recent_sessions)}",
        "",
        "## 🧭 Executive Summary",
        f"Autonomous dream-cycle reflection analyzed **{len(recent_sessions)} recent sessions** across the Hermes/OpenClaw brain, discovering **{len(correlations)} latent technical associations** between sessions.",
        "",
        "## 🔗 Latent Cross-Session Associations",
        "The following sessions exhibit strong conceptual, tag, or contextual correlation:",
        "",
        "| Session A | Session B | Similarity | Shared Dimensions |",
        "| :--- | :--- | :---: | :--- |",
    ]

    for c in correlations[:12]:
        tags_str = ", ".join(f"`#{t}`" for t in c["shared_tags"]) if c["shared_tags"] else ", ".join(c["shared_words"])
        rel_a = os.path.relpath(c["a"]["path"], vault_root).replace("\\", "/")
        rel_b = os.path.relpath(c["b"]["path"], vault_root).replace("\\", "/")
        lines.append(f"| [[{rel_a}\\|{c['a']['name']}]] | [[{rel_b}\\|{c['b']['name']}]] | `{c['score']:.1f}` | {tags_str} |")

    # 4. Aggregated Action Items across Sessions
    all_tasks = []
    for s in recent_sessions:
        for t in s["tasks"]:
            all_tasks.append((t, s["name"], s["path"]))

    lines.extend([
        "",
        "## 📋 Consolidated Action Items (Past Window)",
    ])
    if all_tasks:
        for t_text, s_name, s_path in all_tasks[:15]:
            rel = os.path.relpath(s_path, vault_root).replace("\\", "/")
            lines.append(f"- [ ] {t_text} — [[{rel}|{s_name}]]")
    else:
        lines.append("- (No open action items pending in recent sessions)")

    lines.extend([
        "",
        "---",
        "*Report compiled by `Scripts/dream_cycle.py`. Add `--link` to inject reciprocal links into session notes.*",
        ""
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Report] Successfully generated synthesis note: {report_path}")

    # 5. Optional Auto-linking
    if args.link and correlations:
        linked_count = 0
        for c in correlations[:8]:
            for source, target in [(c["a"], c["b"]), (c["b"], c["a"])]:
                target_rel = os.path.relpath(target["path"], vault_root).replace("\\", "/")
                link_line = f"\n- [[{target_rel}|{target['name']}]] (Score: {c['score']:.1f})"
                try:
                    s_content = source["path"].read_text(encoding="utf-8")
                    if target["name"] not in s_content:
                        if "## Related Sessions" not in s_content:
                            s_content += "\n\n## 🔗 Related Sessions (Dream Cycle)\n"
                        s_content += link_line
                        source["path"].write_text(s_content, encoding="utf-8")
                        linked_count += 1
                except Exception as e:
                    pass
        print(f"  [Backlinks] Injected {linked_count} reciprocal session links.")

    print("✅ Dream Cycle consolidation complete.")

if __name__ == "__main__":
    main()
