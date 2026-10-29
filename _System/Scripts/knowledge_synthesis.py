#!/usr/bin/env python3
"""
knowledge_synthesis.py — BASB/ZK-inspired knowledge synthesis for multi-harness agents.

Consolidates session archives into durable, linked knowledge:
1. Extracts atomic ideas from session notes (one idea per candidate note).
2. Applies progressive summarization — distills long sessions into layered summaries
   (summary → key takeaways → actionable facts).
3. Builds MOCs (Maps of Content / structure notes) for topics that recur across
   sessions, following Zettelkasten linking principles.
4. Auto-inserts bidirectional wikilinks between related notes.
5. Produces a synthesis report of what was linked, summarized, and structured.

Usage:
  python knowledge_synthesis.py --vault <vault_path> [--days 14] [--link] [--moc]

Multi-harness: accepts --vault CLI arg, works from CLI, desktop, TUI, or gateway.
Writes vault-local only. No remote pushes. No Hermes binary dependency.

Design principles (BASB/ZK):
- PARA-aware: respects Projects/Areas/Resources/Archives folder structure.
- Atomic notes: each candidate fact becomes its own linkable note.
- Progressive summarization: raw session → distilled takeaways → durable facts.
- Networked thought: every note gets at least one wikilink back to its source
  session and forward links to related MOCs/notes.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
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
    global VAULT, DAILY_DIR, MEMORY_REVIEW_DIR, SYNTHESIS_DIR
    VAULT = Path(vault_path).resolve()
    DAILY_DIR = VAULT / "04-Archives" / "Daily"
    if not DAILY_DIR.exists():
        DAILY_DIR = VAULT / "Daily"
    MEMORY_REVIEW_DIR = VAULT / "04-Archives" / "Memory-Review"
    if not MEMORY_REVIEW_DIR.exists():
        MEMORY_REVIEW_DIR = VAULT / "Memory-Review"
    SYNTHESIS_DIR = VAULT / "03-Resources" / "Synthesis"
    SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)


# Path variables — set by init_paths(), never at import time.
VAULT = None
DAILY_DIR = None
MEMORY_REVIEW_DIR = None
SYNTHESIS_DIR = None


# ---------------------------------------------------------------------------
# Session Parsing & Analysis
# ---------------------------------------------------------------------------

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SESSION_ID_RE = re.compile(r'session_id:\s*"([^"]+)"')
CREATED_RE = re.compile(r"created_at:\s*\"(\d{4})-(\d{2})-(\d{2})")

def extract_session_data(file_path: Path):
    """Parse a session note for tags, tasks, ideas, and metadata."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # Skip scaffolding files
    if file_path.name in ["README.md", "Timeline.md", "Chat-Correlation.md", "manifest.jsonl"]:
        return None

    # Extract tags
    tags = set(re.findall(r"(?:^tags:\s*\[(.*?)\]|#([a-zA-Z0-9_\-]+))", text, re.M))
    flat_tags = set()
    for t_tuple in tags:
        for t in t_tuple:
            for item in t.split(","):
                clean = item.strip().replace("#", "")
                if clean and clean.lower() not in ["daily", "session", "chat"]:
                    flat_tags.add(clean.lower())

    # Extract action tasks (unchecked checkboxes)
    tasks = []
    for line in text.splitlines():
        m = re.match(r"^\s*-\s+\[\s\]\s+(.*?)$", line)
        if m:
            tasks.append(m.group(1).strip())

    # Extract potential atomic ideas from headings, rule statements, and key lines
    ideas = []
    idea_patterns = [
        re.compile(r"^#{2,3}\s+(.+)$", re.M),                          # headings
        re.compile(r"(?:rule|standard|always|never|convention):\s*(.+)", re.I),
        re.compile(r"(?:learned|takeaway|key insight):\s*(.+)", re.I),
    ]
    for line in text.splitlines():
        line = line.strip()
        for pat in idea_patterns:
            m = pat.search(line)
            if m:
                idea_text = m.group(1).strip()
                if 10 < len(idea_text) < 200:
                    ideas.append(idea_text)
                    break

    # Extract technical vocabulary for topic clustering
    words = re.findall(r"\b[A-Za-z0-9_-]{4,25}\b", text.lower())
    stopwords = {
        "this", "that", "with", "from", "have", "here", "were", "what", "when",
        "your", "user", "assistant", "message", "session", "model", "hermes",
        "false", "true", "none", "null", "then", "will", "would", "about",
        "the", "and", "or", "for", "are", "was", "been", "can", "could", "should",
    }
    vocab = [w for w in words if w not in stopwords and not w.isdigit()]

    # Extract created date from frontmatter
    created_match = CREATED_RE.search(text)
    created_date = None
    if created_match:
        created_date = f"{created_match.group(1)}-{created_match.group(2)}-{created_match.group(3)}"

    # Extract session_id for linking
    sid_match = SESSION_ID_RE.search(text)
    session_id = sid_match.group(1) if sid_match else None

    return {
        "path": file_path,
        "name": file_path.stem,
        "rel_path": file_path.as_posix(),
        "tags": flat_tags,
        "tasks": tasks,
        "ideas": ideas,
        "vocab_counts": Counter(vocab),
        "created_date": created_date,
        "session_id": session_id,
        "raw_text": text,
    }


def calculate_similarity(sess_a, sess_b):
    """Compute similarity score across tags, vocabulary, and ideas."""
    common_tags = sess_a["tags"] & sess_b["tags"]
    tag_score = len(common_tags) * 3.0

    top_a = set(w for w, _ in sess_a["vocab_counts"].most_common(25))
    top_b = set(w for w, _ in sess_b["vocab_counts"].most_common(25))
    common_words = top_a & top_b
    word_score = len(common_words) * 0.5

    ideas_a = set(i.lower() for i in sess_a["ideas"])
    ideas_b = set(i.lower() for i in sess_b["ideas"])
    common_ideas = ideas_a & ideas_b
    idea_score = len(common_ideas) * 2.0

    return tag_score + word_score + idea_score, common_tags, common_words, common_ideas


# ---------------------------------------------------------------------------
# Atomic Idea Extraction (Zettelkasten: one idea per note)
# ---------------------------------------------------------------------------

def extract_atomic_ideas(sessions, min_confidence=2):
    """Extract atomic ideas from sessions, each becoming a potential note."""
    atomic_ideas = []
    for s in sessions:
        for idea in s["ideas"]:
            # Weight ideas by session context
            weight = len(s["tags"]) + len(s["tasks"]) * 0.5
            if weight >= min_confidence:
                atomic_ideas.append({
                    "idea": idea,
                    "source_session": s["name"],
                    "source_path": s["rel_path"],
                    "tags": s["tags"],
                    "weight": weight,
                })
    # Deduplicate near-identical ideas
    seen = set()
    unique = []
    for ai in atomic_ideas:
        key = ai["idea"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(ai)
    return sorted(unique, key=lambda x: x["weight"], reverse=True)


# ---------------------------------------------------------------------------
# Progressive Summarization (BASB: layered distillation)
# ---------------------------------------------------------------------------

def progressive_summarize(session_data):
    """Distill a session into layered summary:
    Layer 1: Raw session (unchanged)
    Layer 2: Key takeaways (ideas + tasks)
    Layer 3: Durable facts (atomic, linkable ideas)
    """
    ideas = session_data["ideas"]
    tasks = session_data["tasks"]
    tags = session_data["tags"]

    # Layer 2: Key takeaways (top ideas + unfinished tasks)
    key_takeaways = []
    for idea in ideas[:5]:
        key_takeaways.append(f"• {idea}")
    for task in tasks[:3]:
        key_takeaways.append(f"• ⏳ {task}")

    # Layer 3: Durable facts (ideas that look like rules/principles/facts)
    durable_facts = []
    fact_patterns = [
        re.compile(r"(?:always|never|should|must|convention|standard|rule):", re.I),
        re.compile(r"(?:learned|takeaway|insight|conclusion):", re.I),
    ]
    for idea in ideas:
        for pat in fact_patterns:
            if pat.search(idea):
                durable_facts.append(idea)
                break

    return {
        "session": session_data["name"],
        "date": session_data["created_date"],
        "tags": sorted(tags),
        "key_takeaways": key_takeaways,
        "durable_facts": durable_facts,
        "idea_count": len(ideas),
        "task_count": len(tasks),
    }


# ---------------------------------------------------------------------------
# MOC Building (Maps of Content / structure notes)
# ---------------------------------------------------------------------------

def build_mocs(sessions, moc_dir_name="MOCs"):
    """Build Map of Content notes for recurring topics across sessions."""
    # Cluster sessions by shared tags/vocabulary
    topic_clusters = defaultdict(list)
    for s in sessions:
        # Use top vocab words as topic keys
        top_words = [w for w, _ in s["vocab_counts"].most_common(8)]
        for word in top_words:
            topic_clusters[word].append(s)

    # Filter to clusters with 2+ sessions (recurring topics)
    moc_clusters = []
    for topic, members in topic_clusters.items():
        if len(members) >= 2:
            moc_clusters.append({
                "topic": topic,
                "members": members,
                "member_count": len(members),
            })

    # Sort by cluster size (most recurring topics first)
    moc_clusters.sort(key=lambda x: x["member_count"], reverse=True)

    return moc_clusters[:10]  # Top 10 MOCs


def write_moc_note(moc_cluster, vault_path):
    """Write a MOC note for a topic cluster."""
    topic = moc_cluster["topic"]
    members = moc_cluster["members"]

    # Sanitize topic for filename
    safe_topic = re.sub(r"[^a-zA-Z0-9_\-]+", "-", topic).strip("-").lower()
    moc_path = VAULT / "03-Resources" / "MOCs" / f"MOC-{safe_topic}.md"
    moc_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "---",
        "type: moc",
        "status: active",
        f"topic: {topic}",
        f"created: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "tags: [moc, structure-note, knowledge-synthesis]",
        "---",
        "",
        f"# 🗺️ Map of Content: {topic.title()}",
        "",
        f"> Auto-generated by `Scripts/knowledge_synthesis.py` on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.",
        f"> This MOC aggregates {moc_cluster['member_count']} sessions around the topic **{topic}**.",
        "",
        "## 📚 Member Sessions",
        "",
    ]

    for member in sorted(members, key=lambda x: x["created_date"] or "", reverse=True):
        rel = os.path.relpath(member["path"], VAULT).replace("\\", "/")
        date_str = member["created_date"] or "unknown date"
        lines.append(f"- [[{rel}|{member['name']}]] — {date_str}")

    lines.extend([
        "",
        "## 🔗 Related MOCs",
        "",
        "_Add cross-references to related MOCs here as your knowledge graph grows._",
        "",
        "## 📝 Notes",
        "",
        "_Capture synthesis insights, open questions, and next actions here._",
        "",
        "---",
        "*Generated by knowledge_synthesis.py — regenerate to refresh.*",
    ])

    moc_path.write_text("\n".join(lines), encoding="utf-8")
    return moc_path


# ---------------------------------------------------------------------------
# Backlink Injection
# ---------------------------------------------------------------------------

def inject_backlinks(sessions, moc_clusters):
    """Inject bidirectional wikilinks between related sessions and MOCs."""
    linked_count = 0

    # Build topic → sessions mapping
    topic_to_sessions = defaultdict(list)
    for moc in moc_clusters:
        for member in moc["members"]:
            topic_to_sessions[member["name"]].append(moc["topic"])

    for session in sessions:
        session_name = session["name"]
        topics = topic_to_sessions.get(session_name, [])
        if not topics:
            continue

        try:
            content = session["path"].read_text(encoding="utf-8")
        except Exception:
            continue

        # Check if MOC links already exist
        if "## 🗺️ Related Topics" in content:
            continue

        # Build MOC link lines
        link_lines = ["\n## 🗺️ Related Topics", ""]
        for topic in topics:
            safe_topic = re.sub(r"[^a-zA-Z0-9_\-]+", "-", topic).strip("-").lower()
            moc_path = f"03-Resources/MOCs/MOC-{safe_topic}.md"
            link_lines.append(f"- [[{moc_path}|MOC: {topic}]]")
        link_lines.append("")

        # Append before the last trailing newlines or at end of file
        content = content.rstrip() + "\n\n" + "\n".join(link_lines)
        session["path"].write_text(content, encoding="utf-8")
        linked_count += 1

    return linked_count


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Knowledge Synthesis — BASB/ZK-inspired atomic notes and MOCs"
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
        "--link",
        action="store_true",
        help="Inject bidirectional wikilinks between sessions and MOCs",
    )
    parser.add_argument(
        "--moc",
        action="store_true",
        help="Build Map of Content notes for recurring topics",
    )
    parser.add_argument(
        "--atomic",
        action="store_true",
        help="Extract atomic ideas as candidate notes in Memory-Review",
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

    vault_root = init_paths_and_resolve(args.vault)
    daily_cand = VAULT / "04-Archives" / "Daily"
    daily_dir = daily_cand if daily_cand.exists() else VAULT / "Daily"
    if not daily_dir.exists():
        print(f"❌ Daily directory not found at: {daily_dir}")
        return

    print(f"🧠 Running Hermes Brain Knowledge Synthesis — Scope: Last {args.days} days")
    print(f"📁 Target Vault: {VAULT}")

    # 1. Collect recent session notes
    cutoff = datetime.now() - timedelta(days=args.days)
    recent_sessions = []
    for f in daily_dir.rglob("*.md"):
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
    if not recent_sessions:
        print("  No sessions found in the specified window.")
        return

    # 2. Progressive summarization for each session
    summaries = []
    for s in recent_sessions:
        summaries.append(progressive_summarize(s))

    # 3. Extract atomic ideas
    atomic_ideas = extract_atomic_ideas(recent_sessions)

    # 4. Build MOCs
    moc_clusters = build_mocs(recent_sessions)

    # 5. Write MOC notes if requested
    written_mocs = []
    if args.moc:
        for moc in moc_clusters:
            moc_path = write_moc_note(moc, VAULT)
            written_mocs.append(moc_path)

    # 6. Extract atomic ideas as candidate notes if requested
    staged_ideas = []
    if args.atomic:
        MEMORY_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        for idea in atomic_ideas[:10]:  # Top 10 atomic ideas
            safe_slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", idea["idea"][:40]).strip("-").lower()
            target_file = MEMORY_REVIEW_DIR / f"atomic_{safe_slug}.md"
            if target_file.exists():
                continue
            now_utc = datetime.now(timezone.utc)
            note_content = f"""---
type: atomic-idea
status: pending-review
created: {now_utc.isoformat()}
source: "{idea['source_session']}"
tags: [{', '.join(sorted(idea['tags']))[:50]}]
---

# 💡 Atomic Idea: {idea['idea']}

### Source
- **Session:** [[{idea['source_path']}|{idea['source_session']}]]
- **Weight:** {idea['weight']:.1f}
- **Tags:** {', '.join(f'`#{t}`' for t in sorted(idea['tags']))}

### Idea
{idea['idea']}

### Review Checklist
- [ ] **Atomic** (single, focused idea)
- [ ] **Durable** (relevant beyond this session)
- [ ] **Non-Sensitive** (no credentials)
- [ ] **Linked** (connected to related notes/MOCs)

---
*Generated by knowledge_synthesis.py — review and promote or reject.*"""
            target_file.write_text(note_content, encoding="utf-8")
            staged_ideas.append(target_file)

    # 7. Inject backlinks if requested
    linked_count = 0
    if args.link:
        linked_count = inject_backlinks(recent_sessions, moc_clusters)

    # 8. Generate synthesis report
    now = datetime.now()
    report_name = f"Knowledge-Synthesis-{now.strftime('%Y-%m-%d')}.md"
    report_path = SYNTHESIS_DIR / report_name

    lines = [
        "---",
        "type: synthesis",
        "status: generated",
        f"created: {now.strftime('%Y-%m-%d')}",
        "tags: [synthesis, knowledge, baSB, zettelkasten, auto-generated]",
        "---",
        "",
        f"# 🧠 Knowledge Synthesis — {now.strftime('%Y-%m-%d')}",
        "",
        f"> Generated by `Scripts/knowledge_synthesis.py` on {now.strftime('%Y-%m-%d %H:%M')}.",
        f"> Sessions analyzed: **{len(recent_sessions)}** over the last **{args.days}** days.",
        "",
        "## 📊 Summary Statistics",
        "",
        f"- **Sessions analyzed:** {len(recent_sessions)}",
        f"- **Atomic ideas extracted:** {len(atomic_ideas)}",
        f"- **MOCs built:** {len(moc_clusters)}",
        f"- **Backlinks injected:** {linked_count}",
        f"- **Ideas staged as candidates:** {len(staged_ideas)}",
        "",
        "## 🔥 Top Topics (by session frequency)",
        "",
    ]

    for moc in moc_clusters[:8]:
        lines.append(f"- **{moc['topic']}** — {moc['member_count']} sessions")

    lines.extend([
        "",
        "## 💡 Atomic Ideas (top candidates)",
        "",
    ])

    for idea in atomic_ideas[:10]:
        lines.append(f"- {idea['idea']} _(from {idea['source_session']}, weight {idea['weight']:.1f})_")

    lines.extend([
        "",
        "## 🗺️ MOCs Created",
        "",
    ])

    for moc_path in written_mocs:
        lines.append(f"- [[{moc_path.relative_to(VAULT).as_posix()}|{moc_path.name}]]")

    lines.extend([
        "",
        "## 📝 Progressive Summaries",
        "",
    ])

    for summary in summaries[:5]:
        lines.append(f"### {summary['session']}")
        if summary["durable_facts"]:
            lines.append("- **Durable facts:**")
            for fact in summary["durable_facts"][:3]:
                lines.append(f"  - {fact}")
        if summary["key_takeaways"]:
            lines.append("- **Key takeaways:**")
            for takeaway in summary["key_takeaways"][:3]:
                lines.append(f"  {takeaway}")
        lines.append("")

    lines.extend([
        "---",
        "*Generated by `Scripts/knowledge_synthesis.py` — BASB/ZK-inspired knowledge synthesis.*",
        "",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Report] Synthesis note written: {report_path}")

    print("\n✅ Knowledge Synthesis complete.")
    print(f"   Sessions: {len(recent_sessions)}")
    print(f"   Atomic ideas: {len(atomic_ideas)}")
    print(f"   MOCs: {len(moc_clusters)} ({len(written_mocs)} written)")
    print(f"   Backlinks: {linked_count}")
    print(f"   Ideas staged: {len(staged_ideas)}")


def init_paths_and_resolve(vault_arg):
    """Resolve vault path and init path globals. Returns vault root Path."""
    vault_path = vault_arg or os.environ.get("HERMES_VAULT_PATH") or None
    if not vault_path:
        detected = find_vault_root()
        if detected:
            vault_path = str(detected)
    if not vault_path:
        print("Vault path not specified and auto-detection failed — aborting.", file=sys.stderr)
        print("  Pass --vault <path> or set HERMES_VAULT_PATH.", file=sys.stderr)
        sys.exit(1)
    init_paths(vault_path)
    return VAULT


def run_self_test():
    import tempfile, shutil
    print("=" * 60)
    print("🧪 knowledge_synthesis.py Self-Test Suite")
    print("=" * 60)

    test_dir = Path(tempfile.mkdtemp(prefix="hb-synthesis-test-"))
    try:
        vault = test_dir / "Vault"
        vault.mkdir()
        (vault / "01-Projects").mkdir(parents=True)
        (vault / "02-Areas").mkdir(parents=True)
        (vault / "03-Resources" / "MOCs").mkdir(parents=True)
        (vault / "04-Archives" / "Daily" / "2026" / "09" / "25").mkdir(parents=True)
        (vault / "04-Archives" / "Daily" / "2026" / "09" / "26").mkdir(parents=True)
        (vault / "04-Archives" / "Memory-Review").mkdir(parents=True)

        # Session A: SQLite + WAL + MCP
        sess_a = vault / "04-Archives" / "Daily" / "2026" / "09" / "25" / "session-sqlite.md"
        sess_a.write_text(
            """---
session_id: "sess-sqlite-001"
created_at: "2026-09-25T10:00:00Z"
tags: [sqlite, database, architecture, mcp]
---
# SQLite Session

Rule: Always enable WAL mode on SQLite databases for concurrent access.

Standard: Use sqlite3 CLI for local database inspection.

Takeaway: WAL mode improves read performance significantly.

- [ ] Setup SQLite WAL mode on production
- [ ] Benchmark WAL vs journal mode

Tags: #sqlite #database #wal #architecture
""", encoding="utf-8")

        # Session B: PostgreSQL + MCP (contradiction + shared MCP topic)
        sess_b = vault / "04-Archives" / "Daily" / "2026" / "09" / "26" / "session-postgres.md"
        sess_b.write_text(
            """---
session_id: "sess-postgres-002"
created_at: "2026-09-26T14:00:00Z"
tags: [postgres, database, mcp, architecture]
---
# PostgreSQL Session

Deploying postgres server for cloud queries.

Standard: Always use connection pooling with PostgreSQL.

Also connecting via mcp stdio json-rpc server.

- [ ] Configure PostgreSQL connection pool
- [ ] Test MCP stdio integration

Tags: #postgres #database #mcp #architecture
""", encoding="utf-8")

        # Test extract_session_data
        data_a = extract_session_data(sess_a)
        data_b = extract_session_data(sess_b)
        assert data_a is not None and data_b is not None
        print("✅ extract_session_data -> OK")

        # Initialize paths for functions that use VAULT global
        init_paths(str(vault))

        # Test calculate_similarity
        score, tags, words, ideas = calculate_similarity(data_a, data_b)
        assert score > 0
        assert "database" in tags or "architecture" in tags
        print(f"✅ calculate_similarity -> OK (score={score:.1f}, shared_tags={tags})")

        # Test extract_atomic_ideas
        ideas = extract_atomic_ideas([data_a, data_b])
        assert len(ideas) >= 1
        print(f"✅ extract_atomic_ideas -> OK ({len(ideas)} ideas extracted)")

        # Test progressive_summarize
        summary = progressive_summarize(data_a)
        assert "session" in summary
        assert "key_takeaways" in summary
        assert "durable_facts" in summary
        print("✅ progressive_summarize -> OK")

        # Test build_mocs
        mocs = build_mocs([data_a, data_b])
        assert len(mocs) >= 1  # "database" should be a recurring topic
        print(f"✅ build_mocs -> OK ({len(mocs)} MOC clusters)")

        # Test write_moc_note
        if mocs:
            moc_path = write_moc_note(mocs[0], vault)
            assert moc_path.exists()
            print(f"✅ write_moc_note -> OK ({moc_path.name})")

        # Test inject_backlinks
        linked = inject_backlinks([data_a, data_b], mocs)
        print(f"✅ inject_backlinks -> OK ({linked} sessions linked)")

        print("=" * 60)
        print("🎉 All knowledge_synthesis.py self-tests PASSED successfully!")
        print("=" * 60)

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    main()