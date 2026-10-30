#!/usr/bin/env python3
"""
Hermes Brain — Conversation Learning Skill (aprende-style self-improvement).

Reviews the vault's archived sessions, extracts learnings across four categories
(memory, lesson, skill, project-doc), and stages them as confirmation-first
candidates for human review. Nothing is written unless the user approves.

Multi-harness compatible:
  - --vault CLI arg for vault path (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - Works from any TUI agent (CLI, desktop, TUI, gateway)

Subcommands:
  converse_learn.py scan        Scan sessions, generate candidate learnings (dry-run)
  converse_learn.py apply       Apply confirmed learnings (per-item approval)
  converse_learn.py --test      Built-in self-test suite

Four categories:
  - memory   — durable facts, preferences, project context, external references
  - lesson   — mistakes that happened: what, why, and how to avoid (anti-pattern)
  - skill    — reusable multi-step workflow surfaced from repeated patterns
  - project-doc — build commands, repo conventions, gotchas worth documenting

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
DAILY_DIR = None
MEMORY_REVIEW_DIR = None
REPORT_DIR = None
LEARNING_REPORT = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root.
    Called from main() after argument parsing — never at import time.
    """
    global VAULT, DAILY_DIR, MEMORY_REVIEW_DIR, REPORT_DIR, LEARNING_REPORT
    VAULT = os.path.abspath(vault_path)
    DAILY_DIR = os.path.join(VAULT, "04-Archives", "Daily")
    if not os.path.isdir(DAILY_DIR):
        DAILY_DIR = os.path.join(VAULT, "Daily")
    MEMORY_REVIEW_DIR = os.path.join(VAULT, "04-Archives", "Memory-Review")
    if not os.path.isdir(MEMORY_REVIEW_DIR):
        MEMORY_REVIEW_DIR = os.path.join(VAULT, "Memory-Review")
    REPORT_DIR = os.path.join(VAULT, "04-Archives", "Audit-Reports")
    LEARNING_REPORT = os.path.join(REPORT_DIR, "Conversation-Learning-Report.md")


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


def slugify(text):
    """Create a safe filename slug from text."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-")
    return slug or "untitled"


# ---------------------------------------------------------------------------
# Session parsing
# ---------------------------------------------------------------------------
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SESSION_ID_RE = re.compile(r'session_id:\s*"([^"]+)"')
CREATED_RE = re.compile(r"created_at:\s*\"(\d{4})-(\d{2})-(\d{2})")
TAG_FRONTMATTER_RE = re.compile(r"^tags:\s*\[(.*?)\]", re.M)
HASHTAG_RE = re.compile(r"#([A-Za-z0-9_\-]+)")


def read_session_files(daily_dir, days):
    """Walk Daily/ and return session data dicts within the day window."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    sessions = []
    if not os.path.isdir(daily_dir):
        return sessions
    for root, dirs, files in os.walk(daily_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, VAULT).replace("\\", "/")
            # Skip scaffolding
            if f in ("README.md", "Timeline.md", "Chat-Correlation.md", "manifest.jsonl"):
                continue
            content = read_file(full)
            if not content.strip():
                continue
            # Extract metadata
            sid_match = SESSION_ID_RE.search(content)
            created_match = CREATED_RE.search(content)
            created_date = None
            if created_match:
                created_date = f"{created_match.group(1)}-{created_match.group(2)}-{created_match.group(3)}"
            # Date filter
            if created_date:
                try:
                    cdt = datetime.datetime.strptime(created_date, "%Y-%m-%d")
                    if cdt < cutoff:
                        continue
                except ValueError:
                    pass
            # Tags
            tags = set()
            tf_match = TAG_FRONTMATTER_RE.search(content)
            if tf_match:
                for t in tf_match.group(1).split(","):
                    t = t.strip()
                    if t:
                        tags.add(t.lower())
            for h in HASHTAG_RE.findall(content):
                tags.add(h.lower())
            # Tool calls / messages
            tool_calls = []
            for m in re.finditer(r"```json\s*\n(.*?)\n```", content, re.S):
                try:
                    calls = json.loads(m.group(1))
                    if isinstance(calls, list):
                        for c in calls:
                            if isinstance(c, dict) and c.get("function"):
                                tool_calls.append(c["function"].get("name", "unknown"))
                except Exception:
                    pass
            sessions.append({
                "path": full,
                "rel_path": rel,
                "name": os.path.splitext(f)[0],
                "session_id": sid_match.group(1) if sid_match else None,
                "created_date": created_date,
                "tags": tags,
                "tool_calls": tool_calls,
                "raw_text": content,
            })
    return sessions


# ---------------------------------------------------------------------------
# Pass A: Scan — extract signal patterns from sessions
# ---------------------------------------------------------------------------
CORRECTION_RE = re.compile(
    r"(?:no,\s*(?:do|use)\s+(.+)|actually\s+(.+?)(?:\.|$)|always\s+(.+?)(?:\.|$)|"
    r"never\s+(.+?)(?:\.|$)|stop\s+doing\s+(.+?)(?:\.|$)|the\s+convention\s+here\s+is\s+(.+?)(?:\.|$))",
    re.I,
)
ERROR_FIX_RE = re.compile(
    r"(?:failed|error|exception|bug|broken).*?(?:fixed|resolved|solved|worked|succeeded)",
    re.I,
)
REPEATED_ATTEMPT_RE = re.compile(
    r"(?:edit|write|bash|run|exec).*?(?:edit|write|bash|run|exec)",
    re.I,
)
WHY_RE = re.compile(
    r"(?:the\s+reason\s+is|because|the\s+gotcha\s+is|the\s+detail\s+is|the\s+trap\s+is)",
    re.I,
)


def scan_sessions(sessions):
    """Extract learning signals from session data."""
    signals = []
    for s in sessions:
        text = s["raw_text"]
        lines = text.splitlines()

        # 1. Explicit user corrections
        for line in lines:
            m = CORRECTION_RE.search(line)
            if m:
                signal_text = m.group(0).strip()
                signals.append({
                    "type": "explicit_correction",
                    "session": s,
                    "message": signal_text,
                    "confidence": "high",
                })

        # 2. Error → fix sequences
        if ERROR_FIX_RE.search(text):
            signals.append({
                "type": "error_fix",
                "session": s,
                "message": "Error→fix sequence detected in session",
                "confidence": "high",
            })

        # 3. Repeated attempts (3+ edits to same file or bash retries)
        edit_count = len(re.findall(r"(?:edit|write|replace|replace_string)", text, re.I))
        bash_retry_count = len(re.findall(r"(?:bash|subprocess|command|run)", text, re.I))
        if edit_count >= 3 or bash_retry_count >= 3:
            signals.append({
                "type": "repeated_attempt",
                "session": s,
                "message": f"Repeated attempts detected ({edit_count} edits, {bash_retry_count} command runs)",
                "confidence": "medium",
            })

        # 4. User explanations of why
        for line in lines:
            if WHY_RE.search(line):
                signals.append({
                    "type": "why_explanation",
                    "session": s,
                    "message": line.strip(),
                    "confidence": "high",
                })
                break  # one per session

        # 5. Workflows described step-by-step (4+ sequential tool calls)
        if len(s["tool_calls"]) >= 4:
            signals.append({
                "type": "step_by_step_workflow",
                "session": s,
                "message": f"Multi-step workflow ({len(s['tool_calls'])} tool calls)",
                "confidence": "medium",
            })

    return signals


# ---------------------------------------------------------------------------
# Pass B: Generate — turn signals into candidate learnings
# ---------------------------------------------------------------------------
def generate_candidates(signals):
    """Convert signals into candidate learning dicts."""
    candidates = []
    for sig in signals:
        session = sig["session"]
        sig_type = sig["type"]
        message = sig["message"]
        confidence = sig["confidence"]

        # Determine category from signal type and message content
        category = categorize(sig_type, message, session)

        # Build a short title
        title = derive_title(message, sig_type)

        candidates.append({
            "category": category,
            "title": title,
            "rationale": message,
            "confidence": confidence,
            "source_session": session["name"],
            "source_path": session["rel_path"],
            "session_id": session.get("session_id"),
        })
    return candidates


def categorize(sig_type, message, session):
    """Map a signal to one of the four categories."""
    text = (message + " " + session["raw_text"]).lower()
    # lesson: mistakes, errors, fixes
    if sig_type in ("error_fix", "explicit_correction") or any(
        w in text for w in ("mistake", "error", "bug", "wrong", "never do", "don't")
    ):
        return "lesson"
    # skill: workflows, repeated patterns, how-to
    if sig_type in ("step_by_step_workflow", "repeated_attempt") or any(
        w in text for w in ("workflow", "steps", "how to", "procedure", "always do")
    ):
        return "skill"
    # project-doc: conventions, build commands, repo rules
    if any(w in text for w in ("convention", "build command", "test command", "repo rule", "project rule")):
        return "project-doc"
    # default: memory
    return "memory"


def derive_title(message, sig_type):
    """Create a short imperative title from the message."""
    # Strip common prefixes
    cleaned = re.sub(r"^(?:the\s+reason\s+is|because|the\s+gotcha\s+is|always|never|stop\s+doing)\s+", "", message, flags=re.I)
    cleaned = cleaned.strip().rstrip(".")
    if len(cleaned) > 60:
        cleaned = cleaned[:57].strip() + "..."
    if not cleaned:
        cleaned = f"{sig_type.replace('_', ' ').title()}"
    return cleaned


# ---------------------------------------------------------------------------
# Pass C: Dedup — check against existing memory files
# ---------------------------------------------------------------------------
def load_existing_memory(memory_review_dir):
    """Load existing memory/lesson/skill/project-doc files for dedup."""
    existing = {
        "memory": set(),
        "lesson": set(),
        "skill": set(),
        "project-doc": set(),
    }
    if not os.path.isdir(memory_review_dir):
        return existing
    for root, dirs, files in os.walk(memory_review_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            content = read_file(full)
            # Extract title from frontmatter or first heading
            tf_match = re.search(r"^title:\s*(.+)$", content, re.M)
            if tf_match:
                title = tf_match.group(1).strip().lower()
                # Determine category from frontmatter type
                type_match = re.search(r"^type:\s*(\w+)", content, re.M)
                ftype = type_match.group(1) if type_match else "memory"
                if ftype in existing:
                    existing[ftype].add(title)
            # Also check first heading
            h_match = re.search(r"^#\s+(.+)$", content, re.M)
            if h_match:
                title = h_match.group(1).strip().lower()
                if title in existing.get("memory", set()) or True:
                    # Add to memory as fallback category
                    existing["memory"].add(title)
    return existing


def dedup_candidates(candidates, existing_memory):
    """Mark candidates that overlap with existing entries."""
    for c in candidates:
        title_lower = c["title"].lower()
        cat = c["category"]
        if title_lower in existing_memory.get(cat, set()):
            c["dedup_note"] = f"[overlaps with existing {cat} entry]"
        else:
            c["dedup_note"] = ""
    return candidates


# ---------------------------------------------------------------------------
# Pass D/E: Report generation and application
# ---------------------------------------------------------------------------
def generate_report(candidates, dry_run=True):
    """Generate the learning report markdown."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(candidates)
    by_cat = Counter(c["category"] for c in candidates)
    by_conf = Counter(c["confidence"] for c in candidates)

    lines = [
        "# Conversation Learning Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Total candidate learnings**: {total}",
    ]
    for cat in ("memory", "lesson", "skill", "project-doc"):
        if by_cat.get(cat, 0) > 0:
            lines.append(f"  - {cat}: {by_cat[cat]}")
    for conf in ("high", "medium", "low"):
        if by_conf.get(conf, 0) > 0:
            lines.append(f"  - {conf}: {by_conf[conf]}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not candidates:
        lines.append("## ✅ No learnings found — nothing to promote.")
        write_report(lines)
        return

    lines.append("## Candidate Learnings")
    lines.append("")
    lines.append("| # | Category | Confidence | Title | Rationale | Source |")
    lines.append("|---|----------|------------|-------|-----------|--------|")
    for i, c in enumerate(candidates, 1):
        rel = c["source_path"]
        lines.append(
            f"| {i} | {c['category']} | {c['confidence']} | {c['title']} | "
            f"{c['rationale'][:80]}... | [[{rel}|{c['source_session']}]] |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Details & Suggested Placement")
    lines.append("")
    for i, c in enumerate(candidates, 1):
        lines.append(f"### {i}. [{c['category'].upper()}] {c['title']}")
        lines.append("")
        lines.append(f"- **Rationale**: {c['rationale']}")
        lines.append(f"- **Confidence**: {c['confidence']}")
        lines.append(f"- **Source**: [[{c['source_path']}|{c['source_session']}]]")
        if c.get("dedup_note"):
            lines.append(f"- **Note**: {c['dedup_note']}")
        lines.append("")
        lines.append(f"**Suggested file**: `04-Archives/Memory-Review/{slugify(c['title'])}.md`")
        lines.append("")

    if dry_run:
        lines.append("## Next Steps")
        lines.append("")
        lines.append("Review the candidates above. To apply them, run with `--apply`.")
        lines.append("Each accepted learning will be written to `04-Archives/Memory-Review/`")
        lines.append("and appended to `MEMORY.md` with a human confirmation gate per item.")
    write_report(lines)


def write_report(lines):
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(LEARNING_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def apply_candidates(candidates, dry_run=True):
    """Apply confirmed learnings: write memory files + append to MEMORY.md."""
    results = []
    memory_index = os.path.join(MEMORY_REVIEW_DIR, "MEMORY.md")

    for c in candidates:
        category = c["category"]
        title = c["title"]
        rationale = c["rationale"]
        source_session = c["source_session"]
        source_path = c["source_path"]
        confidence = c["confidence"]
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        now_iso = datetime.datetime.now().isoformat()

        # Build filename
        safe_slug = slugify(title)
        fname = f"{category}_{safe_slug}.md"
        target_path = os.path.join(MEMORY_REVIEW_DIR, fname)
        # Avoid overwrite
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(MEMORY_REVIEW_DIR, f"{category}_{safe_slug}-{counter}.md")
            counter += 1

        # Build content based on category
        if category == "lesson":
            content = f"""---\ntype: lesson\nname: lesson_{safe_slug}\nconfidence: {confidence}\nstatus: active\ncreatedAt: {now}\nsource_session: {source_session}\nsource_path: {source_path}\n---\n\n**What happened / Qué pasó:**\n{rationale}\n\n**Why it happened / Por qué pasó:**\nExtracted from session [[{source_path}|{source_session}]] during autonomous conversation learning.\n\n**How to avoid / Cómo evitar:**\nReview the source session and apply the correction before repeating this pattern.\n\n**Detection signal / Señal de detección:**\nSession contains patterns matching this issue; watch for recurrence.\n\n---\n*Auto-extracted by converse_learn.py — review and confirm.*\n"""
        elif category == "skill":
            content = f"""---\ntype: skill\nname: skill_{safe_slug}\nconfidence: {confidence}\nstatus: stub\ncreated: {now}\nsource_session: {source_session}\nsource_path: {source_path}\n---\n\n# Skill Stub: {title}\n\n> Auto-extracted skill stub — flesh out before publishing.\n\n**Source**: [[{source_path}|{source_session}]]\n\n**Rationale**: {rationale}\n\n**Steps**:\n1. [STUB — fill in from source session]\n2. [STUB — fill in from source session]\n3. [STUB — fill in from source session]\n\n---\n*Auto-extracted by converse_learn.py — run skill-creator to flesh out before publishing.*\n"""
        elif category == "project-doc":
            content = f"""---\ntype: project-doc\nname: project-doc_{safe_slug}\nconfidence: {confidence}\nstatus: active\ncreated: {now}\nsource_session: {source_session}\nsource_path: {source_path}\n---\n\n# Project Doc: {title}\n\n{rationale}\n\n**Source**: [[{source_path}|{source_session}]]\n\n---\n*Auto-extracted by converse_learn.py — add to CLAUDE.md/AGENTS.md if repo-wide.*\n"""
        else:  # memory
            content = f"""---\ntype: memory\nname: memory_{safe_slug}\nconfidence: {confidence}\nstatus: active\ncreated: {now}\nsource_session: {source_session}\nsource_path: {source_path}\ntags:\n  - memory\n  - {category}\n---\n\n# Memory: {title}\n\n{rationale}\n\n**Source**: [[{source_path}|{source_session}]]\n\n---\n*Auto-extracted by converse_learn.py — review and promote.*\n"""

        if dry_run:
            results.append({
                "category": category,
                "title": title,
                "target": os.path.relpath(target_path, VAULT),
                "applied": False,
                "reason": "dry-run",
            })
        else:
            write_file(target_path, content)
            # Append to MEMORY.md index
            index_entry = f"- [{title}]({os.path.relpath(target_path, VAULT)}) — {rationale[:80]}...\n"
            with open(memory_index, "a", encoding="utf-8") as f:
                f.write(index_entry)
            results.append({
                "category": category,
                "title": title,
                "target": os.path.relpath(target_path, VAULT),
                "applied": True,
                "reason": "applied",
            })

    return results


def generate_remediation_report(results, dry_run=True):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    applied = [r for r in results if r["applied"]]
    lines = [
        "# Conversation Learning — Application Report",
        f"Generated: {now}",
        f"Vault: {VAULT}",
        f"Mode: {'DRY-RUN (no changes)' if dry_run else 'APPLY'}",
        "",
        "---",
        "",
        "## Summary",
        f"- **Total candidates processed**: {len(results)}",
        f"- **Applied**: {len(applied)}",
        "",
        "---",
        "",
    ]
    if applied:
        lines.append("## ✅ Applied Learnings")
        lines.append("")
        lines.append("| Category | Title | File |")
        lines.append("|----------|-------|------|")
        for r in applied:
            lines.append(f"| {r['category']} | {r['title']} | {r['target']} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    if not dry_run:
        lines.append("")
        lines.append("All confirmed learnings have been written to `04-Archives/Memory-Review/`")
        lines.append("and appended to `MEMORY.md` for human review and promotion.")
    write_report(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 converse_learn.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: scan_sessions returns structured data
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "04-Archives", "Daily", "2026", "10", "29"))
        sess = os.path.join(tmp, "04-Archives", "Daily", "2026", "10", "29", "test-session.md")
        write_file(sess, """---\nsession_id: "test-001"\ncreated_at: "2026-10-29T10:00:00Z"\ntags: [python, bug]\n---\n# Test Session\n\nNo, do X instead.\n\nActually that's wrong.\n\n- [ ] Fix this\n- [ ] Fix that\n""")
        # We need VAULT set for read_session_files to compute rel_path
        init_paths(tmp)
        sessions = read_session_files(os.path.join(tmp, "04-Archives", "Daily"), 30)
        assert len(sessions) == 1, f"Expected 1 session, got {len(sessions)}"
        assert sessions[0]["session_id"] == "test-001"
        assert "python" in sessions[0]["tags"]
        print("✅ Test 1: read_session_files parses session metadata")
        passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 2: scan_sessions finds corrections
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "04-Archives", "Daily", "2026", "10", "29"))
        sess = os.path.join(tmp, "04-Archives", "Daily", "2026", "10", "29", "fix-session.md")
        write_file(sess, """---\nsession_id: "test-002"\ncreated_at: "2026-10-29T11:00:00Z"\n---\n# Fix Session\n\nNo, do X instead.\n\nThe convention here is to use pnpm.\n""")
        init_paths(tmp)
        sessions = read_session_files(os.path.join(tmp, "04-Archives", "Daily"), 30)
        signals = scan_sessions(sessions)
        corrections = [s for s in signals if s["type"] == "explicit_correction"]
        assert len(corrections) >= 1, f"Expected >=1 correction, got {len(corrections)}"
        print("✅ Test 2: scan_sessions finds explicit corrections")
        passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 3: generate_candidates produces correct structure
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        fake_session = {
            "name": "test-session",
            "rel_path": "04-Archives/Daily/2026/10/29/test.md",
            "session_id": "test-001",
            "raw_text": "No, do X instead.",
        }
        signals = [{"type": "explicit_correction", "session": fake_session, "message": "No, do X instead.", "confidence": "high"}]
        candidates = generate_candidates(signals)
        assert len(candidates) == 1
        assert candidates[0]["category"] in ("memory", "lesson", "skill", "project-doc")
        assert candidates[0]["title"]
        assert candidates[0]["source_session"] == "test-session"
        print("✅ Test 3: generate_candidates produces correct structure")
        passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        failed += 1
    finally:
        shutil.rmtree(tmp)

    # Test 4: dedup marks duplicates
    tmp = tempfile.mkdtemp()
    try:
        init_paths(tmp)
        existing = {"memory": {"some existing title"}, "lesson": set(), "skill": set(), "project-doc": set()}
        candidates = [
            {"category": "memory", "title": "Some Existing Title", "message": "x", "confidence": "high", "source_session": "s", "source_path": "p"},
            {"category": "lesson", "title": "New Lesson", "message": "x", "confidence": "high", "source_session": "s", "source_path": "p"},
        ]
        result = dedup_candidates(candidates, existing)
        assert result[0].get("dedup_note"), "Expected dedup note for duplicate"
        assert not result[1].get("dedup_note"), "Expected no dedup note for new item"
        print("✅ Test 4: dedup_candidates marks duplicates")
        passed += 1
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
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
        description="Hermes Brain Conversation Learning — extract learnings from sessions.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--days", type=int, default=14, help="Days of sessions to scan (default: 14)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true", help="Apply confirmed learnings (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    sub.add_parser("scan", help="Scan sessions and list candidate learnings")
    sub.add_parser("apply", help="Apply confirmed learnings with per-item approval")
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

    if not os.path.isdir(DAILY_DIR):
        print(f"Error: Daily directory not found at {DAILY_DIR}", file=sys.stderr)
        sys.exit(1)

    sessions = read_session_files(DAILY_DIR, args.days)
    print(f"📋 Scanned {len(sessions)} session files (last {args.days} days)")

    signals = scan_sessions(sessions)
    print(f"🔍 Found {len(signals)} signal patterns")

    candidates = generate_candidates(signals)
    existing = load_existing_memory(MEMORY_REVIEW_DIR)
    candidates = dedup_candidates(candidates, existing)

    if not candidates:
        print("✅ No candidate learnings found.")
        write_report([])
        return

    print(f"💡 Generated {len(candidates)} candidate learnings\n")

    results = []
    for i, c in enumerate(candidates, 1):
        rel = c["source_path"]
        print(f"[{i}/{len(candidates)}] [{c['category'].upper()}] {c['title']}")
        print(f"   Confidence: {c['confidence']} | Rationale: {c['rationale'][:100]}...")
        print(f"   Source: [[{rel}|{c['source_session']}]]")
        if c.get("dedup_note"):
            print(f"   ⚠️  {c['dedup_note']}")

        if dry_run:
            results.append({
                "category": c["category"],
                "title": c["title"],
                "target": f"04-Archives/Memory-Review/{slugify(c['title'])}.md",
                "applied": False,
                "reason": "dry-run preview",
            })
            print(f"   ⏭️  Would apply: {c['title']}\n")
        else:
            # In --apply mode, prompt per item (human-in-the-loop)
            response = input(f"   Apply this learning? [y/N] ").strip().lower()
            if response in ("y", "yes"):
                ok, reason, _ = apply_single(c, dry_run=False)
                results.append({
                    "category": c["category"],
                    "title": c["title"],
                    "target": f"04-Archives/Memory-Review/{slugify(c['title'])}.md",
                    "applied": ok,
                    "reason": reason,
                })
                if ok:
                    print(f"   ✅ Applied: {c['title']}\n")
                else:
                    print(f"   ⏭️  Skipped: {reason}\n")
            else:
                results.append({
                    "category": c["category"],
                    "title": c["title"],
                    "target": f"04-Archives/Memory-Review/{slugify(c['title'])}.md",
                    "applied": False,
                    "reason": "user declined",
                })
                print(f"   ⏭️  Skipped\n")

    # Write report
    report_lines = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    applied_count = sum(1 for r in results if r["applied"])
    report_lines.append("# Conversation Learning Report")
    report_lines.append(f"Generated: {now}")
    report_lines.append(f"Vault: {VAULT}")
    report_lines.append(f"Mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append(f"## Summary: {applied_count}/{len(results)} applied")
    report_lines.append("")
    for r in results:
        status = "✅" if r["applied"] else "⏭️"
        report_lines.append(f"{status} [{r['category']}] {r['title']} — {r['target']} ({r['reason']})")
    write_report(report_lines)
    print(f"\n📄 Report written to {LEARNING_REPORT}")
    print(f"✅ Conversation learning complete: {applied_count}/{len(results)} applied")


def apply_single(finding, dry_run=True):
    """Apply a single candidate finding."""
    target_path = os.path.join(MEMORY_REVIEW_DIR, f"{finding['category']}_{slugify(finding['title'])}.md")
    counter = 1
    while os.path.exists(target_path):
        target_path = os.path.join(MEMORY_REVIEW_DIR, f"{finding['category']}_{slugify(finding['title'])}-{counter}.md")
        counter += 1

    now = datetime.datetime.now().strftime("%Y-%m-%d")
    content = f"""---\ntype: {finding['category']}\nname: {finding['category']}_{slugify(finding['title'])}\nconfidence: {finding['confidence']}\nstatus: pending-review\ncreated: {now}\nsource_session: {finding['source_session']}\nsource_path: {finding['source_path']}\ntags:\n  - learning\n  - {finding['category']}\n---\n\n# Learning: {finding['title']}\n\n**Rationale**: {finding['rationale']}\n\n**Source**: [[{finding['source_path']}|{finding['source_session']}]]\n\n---\n*Auto-extracted by converse_learn.py — review and promote.*\n"""

    if dry_run:
        return True, "dry-run preview", ""
    write_file(target_path, content)
    # Append to MEMORY.md
    index_path = os.path.join(MEMORY_REVIEW_DIR, "MEMORY.md")
    os.makedirs(MEMORY_REVIEW_DIR, exist_ok=True)
    entry = f"- [{finding['title']}]({os.path.relpath(target_path, VAULT)}) — {finding['rationale'][:80]}...\n"
    with open(index_path, "a", encoding="utf-8") as f:
        f.write(entry)
    return True, "applied", ""


if __name__ == "__main__":
    main()
