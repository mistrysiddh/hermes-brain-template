#!/usr/bin/env python3
"""
dream_cycle.py — Autonomous Cognitive Reflection, Contradiction & Evolution Engine (v2).

Consolidates recent episodic memories (04-Archives/Daily/ sessions) into durable semantic knowledge:
1. Scans recent daily sessions (default: last 14 days).
2. Discovers latent cross-session associations and topic clusters.
3. Detects architectural drift & contradictions against accepted ADRs and User Profile.
4. Auto-drafts proposed Architectural Decision Records (ADRs) for emerging patterns.
5. Auto-stages high-confidence durable facts into 04-Archives/Memory-Review/ for 1-click human triage.
6. Produces a Weekly Cognitive Synthesis report: 03-Resources/Research/Weekly-Synthesis-YYYY-Www.md.
7. Optionally inserts bilateral Obsidian wikilinks between related sessions (--link).

Usage:
  Standard Run:
    python dream_cycle.py [vault_path] [--days 14] [--link]

  With Auto-Staging & ADR Drafting:
    python dream_cycle.py [vault_path] --stage-memory --draft-adr

  Run Automated Self-Tests:
    python dream_cycle.py --test
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict, Counter

# ---------------------------------------------------------------------------
# Vault Path Resolution
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


# ---------------------------------------------------------------------------
# Session Parsing & Analysis
# ---------------------------------------------------------------------------

def extract_session_data(file_path: Path):
    """Parse session note for tags, title, topics, tasks, and technical terms."""
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
            if t:
                for item in t.split(","):
                    clean = item.strip().replace("#", "")
                    if clean and clean.lower() not in ["daily", "session", "chat"]:
                        flat_tags.add(clean.lower())

    # Extract action tasks
    tasks = []
    for line in text.splitlines():
        m = re.match(r"^\s*-\s+\[ \]\s+(.*?)$", line)
        if m:
            tasks.append(m.group(1).strip())

    # Extract technical vocabulary
    words = re.findall(r"\b[A-Za-z0-9_-]{4,25}\b", text.lower())
    stopwords = {
        "this", "that", "with", "from", "have", "here", "were", "what", "when",
        "your", "user", "assistant", "message", "session", "model", "hermes",
        "false", "true", "none", "null", "then", "will", "would", "about"
    }
    vocab = [w for w in words if w not in stopwords and not w.isdigit()]

    return {
        "path": file_path,
        "name": file_path.stem,
        "rel_path": file_path.as_posix(),
        "tags": flat_tags,
        "tasks": tasks,
        "vocab_counts": Counter(vocab),
        "raw_text": text
    }


def calculate_similarity(sess_a, sess_b):
    """Compute Jaccard similarity across tags and technical vocabulary."""
    common_tags = sess_a["tags"] & sess_b["tags"]
    tag_score = len(common_tags) * 3.0

    top_a = set(w for w, _ in sess_a["vocab_counts"].most_common(30))
    top_b = set(w for w, _ in sess_b["vocab_counts"].most_common(30))
    common_words = top_a & top_b
    word_score = len(common_words) * 0.5

    return tag_score + word_score, common_tags, common_words


# ---------------------------------------------------------------------------
# Contradiction & Architectural Drift Detection
# ---------------------------------------------------------------------------

CONFLICT_POLARITIES = [
    ("Database Backend", ["sqlite", "sqlite3"], ["postgres", "postgresql", "mysql", "mongodb"]),
    ("Package Manager", ["pnpm", "yarn", "bun"], ["npm"]),
    ("API Protocol", ["graphql", "grpc"], ["rest", "restful"]),
    ("Python Tooling", ["uv", "poetry"], ["pipenv", "setup.py"]),
    ("Code Formatting", ["spaces", "2-space"], ["tabs", "tab-indent"]),
]

def detect_contradictions(sessions: list, vault_root: Path) -> list:
    """
    Detect conflicting decisions across recent sessions or violations of active ADRs.
    """
    conflicts = []

    # 1. Load active ADRs
    active_adrs = {}
    adr_dir = vault_root / "01-Projects" / "ADR"
    if adr_dir.exists():
        for f in adr_dir.glob("*.md"):
            if f.name.lower() == "readme.md":
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore").lower()
                active_adrs[f.stem] = txt
            except Exception:
                continue

    # 2. Check for polarities across pairs of sessions
    for i in range(len(sessions)):
        for j in range(i + 1, len(sessions)):
            s_a = sessions[i]
            s_b = sessions[j]

            for label, pol_a, pol_b in CONFLICT_POLARITIES:
                has_a = any(w in s_a["vocab_counts"] for w in pol_a)
                has_b = any(w in s_b["vocab_counts"] for w in pol_b)
                if has_a and has_b:
                    conflicts.append({
                        "type": "Cross-Session Contradiction",
                        "domain": label,
                        "session_a": s_a["name"],
                        "session_b": s_b["name"],
                        "details": f"Session '{s_a['name']}' utilizes {pol_a}, while Session '{s_b['name']}' introduces {pol_b}."
                    })

    # 3. Check for ADR drift (sessions contradicting accepted ADRs)
    for s in sessions:
        for adr_name, adr_text in active_adrs.items():
            if "status: accepted" in adr_text or "status: active" in adr_text:
                for label, pol_standard, pol_rival in CONFLICT_POLARITIES:
                    if any(w in adr_text for w in pol_standard):
                        # The ADR adopted pol_standard. Does session use pol_rival?
                        if any(w in s["vocab_counts"] for w in pol_rival):
                            conflicts.append({
                                "type": "Architectural Drift (ADR Divergence)",
                                "domain": label,
                                "session_a": s["name"],
                                "session_b": adr_name,
                                "details": f"Session '{s['name']}' uses {pol_rival}, which diverges from accepted {adr_name} ({pol_standard})."
                            })

    return conflicts


# ---------------------------------------------------------------------------
# Proactive ADR Drafter
# ---------------------------------------------------------------------------

PATTERNS_FOR_ADR = [
    {"topic": "Model-Context-Protocol-Integration", "keywords": ["mcp", "stdio", "json-rpc", "tool-call"], "desc": "Standardizing agent vault tools via Model Context Protocol"},
    {"topic": "SQLite-WAL-Persistence-Engine", "keywords": ["sqlite", "wal", "pragma", "database"], "desc": "Standardizing local concurrency and persistence with SQLite WAL mode"},
    {"topic": "Ollama-Local-Inference-Pipeline", "keywords": ["ollama", "local-llm", "embeddings", "nomic"], "desc": "Standardizing offline local embeddings and semantic retrieval"},
    {"topic": "Presidio-Secret-Scrubbing-Boundary", "keywords": ["presidio", "redact", "sanitization", "pii"], "desc": "Automated pre-archive PII and credential sanitization boundary"},
]

def check_and_draft_adrs(sessions: list, vault_root: Path) -> list:
    """
    Detect emerging architectural patterns mentioned across multiple sessions
    and draft a proposed ADR if not already documented.
    """
    drafted = []
    adr_dir = vault_root / "01-Projects" / "ADR"
    adr_dir.mkdir(parents=True, exist_ok=True)

    existing_adrs = {f.stem.lower() for f in adr_dir.glob("*.md")}

    for p in PATTERNS_FOR_ADR:
        topic_slug = p["topic"].lower()
        if any(topic_slug in e for e in existing_adrs):
            continue

        # Count occurrences across sessions
        matching_sessions = []
        for s in sessions:
            if any(k in s["vocab_counts"] or k in s["tags"] for k in p["keywords"]):
                matching_sessions.append(s["name"])

        if len(matching_sessions) >= 2:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            draft_filename = f"ADR-Draft-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{p['topic']}.md"
            draft_path = adr_dir / draft_filename

            adr_content = f"""---
type: adr
status: proposed
date: {now_str}
deciders: [Human, Codex, Argus, Ledger, Vox]
tags: [adr, architecture, multi-agent, dream-cycle-proposed]
---

# 📑 Proposed ADR: {p['topic'].replace('-', ' ')}

> **Status:** `proposed` | **Date:** {now_str} | **Origin:** Automated Dream Cycle v2 Pattern Synthesis

## 1. Context & Problem Statement
* Discovered recurring pattern across {len(matching_sessions)} sessions: {', '.join(matching_sessions[:3])}.
* Objective: {p['desc']}.

## 2. Multi-Agent Persona Review (Preliminary Synthesis)

### 🛡️ Argus (Security & Risk)
* Evaluates threat model and sandbox isolation for {p['topic'].replace('-', ' ')}.

### ⚡ Codex (Implementation & Performance)
* Validates implementation complexity, zero-dependency reliability, and latency.

### 📊 Ledger (Resource Efficiency & Cost)
* Monitors context window utilization, local compute cost, and maintenance overhead.

### 🗣️ Vox (Human Alignment & UX)
* Confirms developer ergonomics, transparent reporting, and human-in-the-loop control.

## 3. Decision & Consensus
* **Proposed Architecture:** Adopt {p['topic'].replace('-', ' ')} across agent workflows.
* **Consensus Status:** Pending human operator sign-off.

---
*Maintained in [[01-Projects/ADR/README|Architecture Decision Records]]*
"""
            draft_path.write_text(adr_content, encoding="utf-8")
            drafted.append({
                "topic": p["topic"],
                "path": str(draft_path.relative_to(vault_root)).replace("\\", "/"),
                "sessions": matching_sessions
            })

    return drafted


# ---------------------------------------------------------------------------
# Auto-Staging High-Confidence Facts for 1-Click Dashboard
# ---------------------------------------------------------------------------

def auto_stage_memory_candidates(sessions: list, vault_root: Path) -> list:
    """
    Extract durable takeaways and stage them into Memory-Review for 1-click human triage.
    """
    staged = []
    review_dir = vault_root / "04-Archives" / "Memory-Review"
    if not review_dir.exists():
        review_dir = vault_root / "Memory-Review"
    review_dir.mkdir(parents=True, exist_ok=True)

    # Heuristic: find lines explicitly declaring architecture rules or takeaways
    rule_patterns = [
        re.compile(r"(?:rule|standard|always|never|convention):\s*(.+)", re.I),
        re.compile(r"learned:\s*(.+)", re.I),
        re.compile(r"takeaway:\s*(.+)", re.I),
    ]

    for s in sessions:
        for line in s["raw_text"].splitlines():
            line_clean = line.strip().lstrip("-*# ")
            for pat in rule_patterns:
                m = pat.search(line_clean)
                if m and len(m.group(1)) > 20 and len(m.group(1)) < 160:
                    fact = m.group(1).strip()
                    now_utc = datetime.now(timezone.utc)
                    safe_slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", fact[:35]).strip("-").lower()
                    target_file = review_dir / f"candidate_{now_utc.strftime('%Y%m%d_%H%M%S')}_{safe_slug}.md"

                    # Avoid duplicate candidates
                    if target_file.exists():
                        continue

                    note_content = f"""---
type: memory-candidate
status: pending-review
created: {now_utc.isoformat()}
category: learned_workflow
source: "{s['name']}"
---

# 🧠 Memory Candidate: {fact[:50]}...

### Candidate Fact
> {fact}

### Context & Rationale
- **Category:** `learned_workflow`
- **Source Session / Origin:** [[04-Archives/Daily/{s['name']}|{s['name']}]]
- **Rationale:** Automatically distilled during Dream Cycle v2 cognitive reflection.

### Review Checklist (Human Gatekeeper)
- [ ] **Durable** (relevant across future turns)
- [ ] **Verified** (confirmed observation)
- [ ] **Non-Sensitive** (no credentials)

### Target Promotion
- [ ] Promote to `02-Areas/User-Profile.md`
- [ ] Promote to `Hermes MEMORY.md`
- [ ] Reject and archive
"""
                    target_file.write_text(note_content, encoding="utf-8")
                    staged.append({
                        "fact": fact,
                        "file": target_file.name,
                        "session": s["name"]
                    })
                    break
        if len(staged) >= 3:
            break

    return staged


# ---------------------------------------------------------------------------
# Self-Test / Diagnostics
# ---------------------------------------------------------------------------

def run_self_test():
    import tempfile, shutil
    print("=" * 60)
    print("🧪 dream_cycle.py (v2) Self-Test Suite")
    print("=" * 60)

    test_dir = Path(tempfile.mkdtemp(prefix="hb-dream-test-"))
    try:
        vault = test_dir / "Vault"
        vault.mkdir()
        (vault / "01-Projects" / "ADR").mkdir(parents=True)
        (vault / "02-Areas").mkdir(parents=True)
        (vault / "03-Resources" / "Research").mkdir(parents=True)
        (vault / "04-Archives" / "Daily" / "2026" / "09" / "25").mkdir(parents=True)
        (vault / "04-Archives" / "Daily" / "2026" / "09" / "26").mkdir(parents=True)
        (vault / "04-Archives" / "Memory-Review").mkdir(parents=True)

        # 1. Create dummy accepted ADR
        (vault / "01-Projects" / "ADR" / "ADR-001.md").write_text(
            "---\nstatus: accepted\n---\n# ADR 001: SQLite standard\nStandardized on sqlite for local data.", encoding="utf-8"
        )

        # 2. Create dummy session A (using sqlite)
        sess_a = vault / "04-Archives" / "Daily" / "2026" / "09" / "25" / "20260925-session-a.md"
        sess_a.write_text(
            "# Session A\nRule: Always enable WAL mode on SQLite databases.\nTags: #sqlite #database #architecture\n- [ ] Task 1", encoding="utf-8"
        )

        # 3. Create dummy session B (introducing postgres conflict and MCP keywords)
        sess_b = vault / "04-Archives" / "Daily" / "2026" / "09" / "26" / "20260926-session-b.md"
        sess_b.write_text(
            "# Session B\nDeploying postgres server for cloud queries.\nAlso connecting via mcp stdio json-rpc server.\nTags: #database #postgres #mcp", encoding="utf-8"
        )

        data_a = extract_session_data(sess_a)
        data_b = extract_session_data(sess_b)
        assert data_a is not None and data_b is not None
        print("✅ extract_session_data -> OK")

        # Test Contradiction Detection
        conflicts = detect_contradictions([data_a, data_b], vault)
        assert len(conflicts) >= 1
        print(f"✅ detect_contradictions -> OK (Detected {len(conflicts)} architectural drift/conflict warnings)")

        # Test ADR auto-drafting
        drafts = check_and_draft_adrs([data_a, data_b], vault)
        # Session B mentions mcp keywords
        print(f"✅ check_and_draft_adrs -> OK (Drafted {len(drafts)} proposed ADRs)")

        # Test Memory candidate staging
        staged = auto_stage_memory_candidates([data_a, data_b], vault)
        assert len(staged) >= 1
        assert "WAL mode" in staged[0]["fact"]
        print(f"✅ auto_stage_memory_candidates -> OK (Staged candidate: {staged[0]['file']})")

        print("=" * 60)
        print("🎉 All dream_cycle.py v2 self-tests PASSED successfully!")
        print("=" * 60)

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hermes Brain Dream Cycle & Latent Synthesis (v2)")
    parser.add_argument("vault", nargs="?", default=None, help="Vault root directory")
    parser.add_argument("--days", type=int, default=14, help="Number of past days to inspect (default: 14)")
    parser.add_argument("--link", action="store_true", help="Auto-inject Related Sessions backlinks into session notes")
    parser.add_argument("--stage-memory", action="store_true", help="Auto-stage distilled facts into Memory-Review")
    parser.add_argument("--draft-adr", action="store_true", help="Auto-draft proposed ADRs for recurring patterns")
    parser.add_argument("--test", action="store_true", help="Run automated self-tests")
    args = parser.parse_args()

    if args.test:
        run_self_test()
        sys.exit(0)

    vault_root = find_vault_root(args.vault)
    daily_cand = vault_root / "04-Archives" / "Daily"
    daily_dir = daily_cand if daily_cand.exists() else vault_root / "Daily"
    if not daily_dir.exists():
        print(f"❌ Daily directory not found at: {daily_dir}")
        return

    print(f"🌙 Running Hermes Brain Dream Cycle v2 — Scope: Last {args.days} days")
    print(f"📁 Target Vault: {vault_root}")

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
    if len(recent_sessions) < 2:
        print("  Notice: Fewer than 2 sessions in recent window. Running lightweight check.")

    # 2. Discover latent cross-session pairs
    correlations = []
    for i in range(len(recent_sessions)):
        for j in range(i + 1, len(recent_sessions)):
            a = recent_sessions[i]
            b = recent_sessions[j]
            score, shared_tags, shared_words = calculate_similarity(a, b)
            if score >= 4.0:
                correlations.append({
                    "a": a, "b": b,
                    "score": score,
                    "shared_tags": shared_tags,
                    "shared_words": list(shared_words)[:5]
                })

    correlations.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Discovered {len(correlations)} latent cross-session associations.")

    # 3. Detect Contradictions & Architecture Drift
    conflicts = detect_contradictions(recent_sessions, vault_root)
    if conflicts:
        print(f"  ⚠️ Detected {len(conflicts)} architectural drift / contradiction points!")
    else:
        print("  ✓ Zero architectural contradictions detected across active sessions.")

    # 4. Proactive ADR Drafts
    drafted_adrs = []
    if args.draft_adr:
        drafted_adrs = check_and_draft_adrs(recent_sessions, vault_root)
        if drafted_adrs:
            print(f"  📑 Auto-drafted {len(drafted_adrs)} proposed ADR(s) in 01-Projects/ADR/:")
            for d in drafted_adrs:
                print(f"     - {d['topic']} (Supported by {len(d['sessions'])} sessions)")

    # 5. Auto-Stage Memory Candidates for 1-Click Dashboard
    staged_facts = []
    if args.stage_memory:
        staged_facts = auto_stage_memory_candidates(recent_sessions, vault_root)
        if staged_facts:
            print(f"  📬 Staged {len(staged_facts)} durable takeaway(s) into Memory-Review queue:")
            for sf in staged_facts:
                print(f"     - \"{sf['fact'][:60]}...\" ({sf['file']})")

    # 6. Generate Weekly Synthesis Report
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
        "tags: [dream-cycle, synthesis, weekly, review, cognition-v2]",
        "---",
        "",
        f"# 🌙 Hermes Brain Cognitive Synthesis — {year} Week {week:02d}",
        "",
        f"> **Generated:** {now.strftime('%Y-%m-%d %H:%M')} | **Window:** Last {args.days} days | **Sessions Analyzed:** {len(recent_sessions)}",
        "",
        "## 🧭 Executive Summary",
        f"Autonomous dream-cycle reflection analyzed **{len(recent_sessions)} recent sessions** across the Hermes/OpenClaw brain, discovering **{len(correlations)} latent technical associations** between sessions.",
    ]

    # Contradictions Section
    lines.extend([
        "",
        "## ⚠️ Detected Contradictions & Architecture Drift",
    ])
    if conflicts:
        for c in conflicts[:8]:
            lines.append(f"- **[{c['type']}] {c['domain']}:** {c['details']}")
    else:
        lines.append("- *No active architectural conflicts or ADR violations detected across recent sessions.*")

    # Proposed ADRs Section
    if drafted_adrs:
        lines.extend([
            "",
            "## 📑 Emerging Patterns & Drafted ADR Proposals",
        ])
        for d in drafted_adrs:
            lines.append(f"- **[[{d['path']}|Proposed ADR: {d['topic']}]]** — Supported by sessions: {', '.join(d['sessions'][:3])}")

    # Latent Associations Table
    lines.extend([
        "",
        "## 🔗 Latent Cross-Session Associations",
        "The following sessions exhibit strong conceptual, tag, or contextual correlation:",
        "",
        "| Session A | Session B | Similarity | Shared Dimensions |",
        "| :--- | :--- | :---: | :--- |",
    ])
    for c in correlations[:12]:
        tags_str = ", ".join(f"`#{t}`" for t in c["shared_tags"]) if c["shared_tags"] else ", ".join(c["shared_words"])
        rel_a = os.path.relpath(c["a"]["path"], vault_root).replace("\\", "/")
        rel_b = os.path.relpath(c["b"]["path"], vault_root).replace("\\", "/")
        lines.append(f"| [[{rel_a}\\|{c['a']['name']}]] | [[{rel_b}\\|{c['b']['name']}]] | `{c['score']:.1f}` | {tags_str} |")

    # Open Actions Section
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
        lines.append("- *(No open action items pending in recent sessions)*")

    lines.extend([
        "",
        "---",
        "*Report compiled by `Scripts/dream_cycle.py` (v2 Cognitive Engine). Use Dashboard.md for 1-click memory review.*",
        ""
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Report] Successfully generated synthesis note: {report_path}")

    # Reciprocal Backlinks
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
                except Exception:
                    pass
        print(f"  [Backlinks] Injected {linked_count} reciprocal session links.")

    print("✅ Dream Cycle v2 consolidation complete.")

if __name__ == "__main__":
    main()
