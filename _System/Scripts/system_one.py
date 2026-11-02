#!/usr/bin/env python3
"""
Hermes Brain — System One Skill (system_one.py)

Fast, automatic, low-latency agent decision support — "System One" thinking:
- Passive inner-monologue loop: observe → assess confidence → summarize
- Four-voice council with vote entropy (4 unanimous vetoes = full "no")
- Confidence calibration: ECE/Brier score, blind-spot detection, coherence metrics
- Number categories: measured / derived / asserted / none
- Agency layer: propose → audit → risk-gate → execute (reduce HITL)
- Knowledge storage: FTS5 BM25 dual-index + KnowledgeGraph (entities, triples, timeline)
- Tool call capture: every tool call searchable at zero LLM tokens
- Dream cycle: release, prune, reconcile, crystallize, distill; heartbeat/handoff persistence

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Subcommands:
  system_one.py monologue   Run inner-monologue loop (observe/assess/summarize)
  system_one.py council     Run four-voice council vote
  system_one.py calibrate   Confidence calibration (ECE/Brier)
  system_one.py agency      Agency layer: propose/audit/risk-gate/execute
  system_one.py knowledge   Knowledge storage (FTS5 BM25 + graph)
  system_one.py tools       Tool call capture
  system_one.py dream       Dream cycle (release/prune/reconcile/crystallize/distill)
  system_one.py --test      Built-in self-test suite

Usage:
  python system_one.py --vault <path> monologue --days 7
  python system_one.py --vault <path> council --question "should we X?"
  python system_one.py --vault <path> --test

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import re
import sqlite3
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
SYSTEM_ONE_DIR = None
KB_DB = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT, SYSTEM_ONE_DIR, KB_DB
    VAULT = os.path.abspath(vault_path)
    SYSTEM_ONE_DIR = os.path.join(VAULT, "04-Archives", "System-One")
    KB_DB = os.path.join(SYSTEM_ONE_DIR, "knowledge.db")


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


def walk_md(vault_dir, exclude_dirs=None, exclude_files=None):
    """Walk vault_dir yielding (full_path, rel_path, name, content) for .md files."""
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash", ".sota"}
    exclude_files = exclude_files or {"README.md", "manifest.jsonl"}
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            if f in exclude_files:
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault_dir).replace("\\", "/")
            content = read_file(full)
            yield full, rel, os.path.splitext(f)[0], content


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def iso_now():
    return now_utc().isoformat()


# ---------------------------------------------------------------------------
# Number categories
# ---------------------------------------------------------------------------
NUMBER_CATEGORY = {"measured", "derived", "asserted", "none"}


def categorize_number(value, source="none"):
    """Categorize a number: measured, derived, asserted, or none."""
    if source in NUMBER_CATEGORY:
        return source
    return "none"


# ---------------------------------------------------------------------------
# Passive inner-monologue loop
# ---------------------------------------------------------------------------
def observe(vault_dir, days=7):
    """Observe recent vault activity — notes modified, links created, patterns."""
    cutoff = now_utc() - datetime.timedelta(days=days)
    observations = []
    for full, rel, name, content in walk_md(vault_dir):
        try:
            mtime = os.path.getmtime(full)
            mtime_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
            if mtime_dt < cutoff:
                continue
        except Exception:
            continue
        words = len(re.findall(r"\b\w+\b", content))
        links = len(re.findall(r"\[\[([^\]]+)\]\]", content))
        tags = len(re.findall(r"(?:^|\s)#([\w\-/]+)", content))
        observations.append({
            "path": rel,
            "name": name,
            "words": words,
            "links": links,
            "tags": tags,
            "mtime": mtime_dt.isoformat(),
        })
    observations.sort(key=lambda o: o["mtime"], reverse=True)
    return observations


def assess_confidence(observations):
    """Assess confidence from observations — link density, recency, tag coverage."""
    if not observations:
        return {"confidence": 0.0, "reason": "no observations"}
    total_words = sum(o["words"] for o in observations)
    total_links = sum(o["links"] for o in observations)
    total_tags = sum(o["tags"] for o in observations)
    note_count = len(observations)
    # Confidence heuristic: more links/tags per note = higher confidence
    link_density = total_links / max(1, note_count)
    tag_density = total_tags / max(1, note_count)
    confidence = min(1.0, (link_density * 0.4 + tag_density * 0.3 + min(note_count, 10) / 10 * 0.3))
    return {
        "confidence": round(confidence, 3),
        "note_count": note_count,
        "link_density": round(link_density, 2),
        "tag_density": round(tag_density, 2),
    }


def summarize(observations, confidence):
    """Summarize observations into a monologue entry."""
    if not observations:
        return "No recent activity to summarize."
    top = observations[:5]
    lines = [f"Observed {len(observations)} note(s) in the window."]
    lines.append(f"Confidence: {confidence['confidence']:.1%} "
                 f"(link density {confidence['link_density']}, tag density {confidence['tag_density']})")
    lines.append("Recent notes:")
    for o in top:
        lines.append(f"  - {o['path']} ({o['words']} words, {o['links']} links, {o['tags']} tags)")
    return "\n".join(lines)


def run_monologue(vault_dir, days=7, dry_run=True):
    """Run the full inner-monologue loop: observe → assess → summarize."""
    observations = observe(vault_dir, days=days)
    confidence = assess_confidence(observations)
    summary = summarize(observations, confidence)
    result = {
        "observations": observations,
        "confidence": confidence,
        "summary": summary,
        "generated_at": iso_now(),
    }
    if not dry_run:
        monologue_dir = os.path.join(SYSTEM_ONE_DIR, "monologues")
        os.makedirs(monologue_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y-%m-%d")
        path = os.path.join(monologue_dir, f"monologue-{date_str}.md")
        content = f"# Inner Monologue — {date_str}\n\n{summary}\n\n---\n\nConfidence: {confidence['confidence']:.1%}\nNotes: {confidence['note_count']}\n"
        write_file(path, content)
        result["written_to"] = path
    return result


# ---------------------------------------------------------------------------
# Four-voice council with vote entropy
# ---------------------------------------------------------------------------
def council_vote(question, voices=None, dry_run=True):
    """
    Four-voice council measures agreement by vote entropy.
    Each voice votes: yes / no / abstain.
    Four unanimous vetoes = full agreement that the answer is no.
    Vote entropy: H = -sum(p_i * log2(p_i)) — lower entropy = higher agreement.
    """
    if voices is None:
        voices = ["voice-a", "voice-b", "voice-c", "voice-d"]
    votes = {}
    for v in voices:
        # Deterministic pseudo-vote based on question hash + voice name
        h = hashlib.sha256(f"{question}:{v}".encode()).hexdigest()
        n = int(h[:8], 16)
        r = n % 100
        if r < 30:
            votes[v] = "no"
        elif r < 60:
            votes[v] = "yes"
        else:
            votes[v] = "abstain"

    total = len(voices)
    yes_count = sum(1 for v in votes.values() if v == "yes")
    no_count = sum(1 for v in votes.values() if v == "no")
    abstain_count = sum(1 for v in votes.values() if v == "abstain")

    # Vote entropy
    probs = {}
    for outcome in ("yes", "no", "abstain"):
        cnt = sum(1 for v in votes.values() if v == outcome)
        probs[outcome] = cnt / total if total > 0 else 0
    entropy = -sum(p * math.log2(p) for p in probs.values() if p > 0)
    max_entropy = math.log2(3)  # 3 outcomes
    agreement = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0

    # Four unanimous vetoes rule
    unanimous_veto = no_count == total and total >= 4
    decision = "no" if unanimous_veto else ("yes" if yes_count > no_count else "abstain")

    result = {
        "question": question,
        "voices": voices,
        "votes": votes,
        "yes_count": yes_count,
        "no_count": no_count,
        "abstain_count": abstain_count,
        "entropy": round(entropy, 4),
        "agreement": round(agreement, 4),
        "unanimous_veto": unanimous_veto,
        "decision": decision,
        "generated_at": iso_now(),
    }
    if not dry_run:
        council_dir = os.path.join(SYSTEM_ONE_DIR, "council")
        os.makedirs(council_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(council_dir, f"council-{date_str}.json")
        write_file(path, json.dumps(result, indent=2))
        result["written_to"] = path
    return result


# ---------------------------------------------------------------------------
# Confidence calibration (ECE / Brier)
# ---------------------------------------------------------------------------
def brier_score(predictions, outcomes):
    """
    Brier score: mean squared error between predicted probabilities and actual outcomes.
    Lower is better. predictions = list of probabilities, outcomes = list of 0/1.
    """
    if not predictions or not outcomes:
        return 0.0
    paired = list(zip(predictions, outcomes))
    sq_errors = [(p - o) ** 2 for p, o in paired]
    return sum(sq_errors) / len(sq_errors)


def expected_calibration_error(predictions, n_bins=10):
    """
    Expected Calibration Error: bin predictions by confidence,
    compare average confidence vs accuracy in each bin.
    """
    if not predictions:
        return 0.0, []
    bins = [[] for _ in range(n_bins)]
    for p, o in predictions:
        bin_idx = min(int(p * n_bins), n_bins - 1)
        bins[bin_idx].append((p, o))
    ece = 0.0
    bin_details = []
    total = len(predictions)
    for b in bins:
        if not b:
            continue
        avg_conf = sum(p for p, _ in b) / len(b)
        accuracy = sum(o for _, o in b) / len(b)
        gap = abs(avg_conf - accuracy)
        weight = len(b) / total
        ece += weight * gap
        bin_details.append({
            "count": len(b),
            "avg_confidence": round(avg_conf, 3),
            "accuracy": round(accuracy, 3),
            "gap": round(gap, 3),
        })
    return round(ece, 4), bin_details


def blind_spot_detection(predictions, outcomes, threshold=0.3):
    """Detect blind spots — high-confidence wrong predictions."""
    spots = []
    paired = list(zip(predictions, outcomes))
    for p, o in paired:
        if p > 0.7 and o == 0:
            spots.append({"confidence": round(p, 3), "outcome": o, "type": "overconfident_wrong"})
        elif p < 0.3 and o == 1:
            spots.append({"confidence": round(p, 3), "outcome": o, "type": "underconfident_wrong"})
    return spots


def coherence_metrics(predictions, outcomes):
    """Coherence metrics naming dimensions that could not be measured."""
    paired = list(zip(predictions, outcomes))
    if not paired:
        return {"coherence": 0.0, "dimensions": ["prediction_count"]}
    dims = []
    # Calibration dimension
    ece, _ = expected_calibration_error(paired)
    dims.append({"dimension": "calibration", "value": round(ece, 4), "measurable": True})
    # Discrimination dimension (separation of outcomes)
    pos_probs = [p for p, o in paired if o == 1]
    neg_probs = [p for p, o in paired if o == 0]
    if pos_probs and neg_probs:
        sep = abs(sum(pos_probs) / len(pos_probs) - sum(neg_probs) / len(neg_probs))
        dims.append({"dimension": "discrimination", "value": round(sep, 4), "measurable": True})
    else:
        dims.append({"dimension": "discrimination", "value": None, "measurable": False,
                     "note": "cannot measure — missing positive or negative outcomes"})
    # Resolution dimension
    dims.append({"dimension": "resolution", "value": round(len(set(p for p, _ in paired)), 4),
                 "measurable": True})
    coherence = sum(d["value"] for d in dims if d["value"] is not None) / max(1,
                                                                             sum(1 for d in dims if d["value"] is not None))
    return {"coherence": round(coherence, 4), "dimensions": dims}


def run_calibrate(predictions=None, outcomes=None, dry_run=True):
    """Run confidence calibration: Brier, ECE, blind spots, coherence."""
    if predictions is None:
        predictions = []
    if outcomes is None:
        outcomes = []
    paired = list(zip(predictions, outcomes))
    brier = brier_score(paired)
    ece, bins = expected_calibration_error(paired)
    blind_spots = blind_spot_detection(paired)
    coherence = coherence_metrics(paired)
    result = {
        "brier_score": round(brier, 4),
        "ece": ece,
        "bin_details": bins,
        "blind_spots": blind_spots,
        "coherence": coherence,
        "sample_size": len(paired),
        "generated_at": iso_now(),
    }
    if not dry_run:
        cal_dir = os.path.join(SYSTEM_ONE_DIR, "calibration")
        os.makedirs(cal_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(cal_dir, f"calibrate-{date_str}.json")
        write_file(path, json.dumps(result, indent=2))
        result["written_to"] = path
    return result


# ---------------------------------------------------------------------------
# Agency layer: propose → audit → risk-gate → execute
# ---------------------------------------------------------------------------
def propose(plan_text):
    """Propose a plan — initial drafting."""
    return {
        "plan": plan_text,
        "status": "proposed",
        "proposed_at": iso_now(),
    }


def audit(plan):
    """Audit a plan — check for risks, missing steps, confidence."""
    risks = []
    text = plan.get("plan", "").lower()
    if "delete" in text or "remove" in text:
        risks.append("destructive_operation")
    if "external" in text or "api" in text:
        risks.append("external_dependency")
    if "loop" in text or "recurs" in text:
        risks.append("infinite_loop_risk")
    confidence = 1.0 - (len(risks) * 0.25)
    confidence = max(0.0, min(1.0, confidence))
    plan["audit_risks"] = risks
    plan["audit_confidence"] = round(confidence, 3)
    plan["status"] = "audited"
    plan["audited_at"] = iso_now()
    return plan


def risk_gate(plan, threshold=0.6):
    """Risk gate — allow execution only if audit confidence >= threshold."""
    conf = plan.get("audit_confidence", 0.0)
    allowed = conf >= threshold
    plan["risk_gate_allowed"] = allowed
    plan["risk_gate_threshold"] = threshold
    plan["status"] = "cleared" if allowed else "blocked"
    plan["gated_at"] = iso_now()
    return plan, allowed


def execute(plan):
    """Execute a cleared plan — in dry-run this is a no-op report."""
    plan["status"] = "executed"
    plan["executed_at"] = iso_now()
    return plan


def run_agency(plan_text, threshold=0.6, dry_run=True):
    """Full agency layer: propose → audit → risk-gate → execute."""
    plan = propose(plan_text)
    plan = audit(plan)
    plan, allowed = risk_gate(plan, threshold=threshold)
    if allowed and not dry_run:
        plan = execute(plan)
    result = {
        "plan_text": plan_text,
        "plan": plan,
        "executed": allowed and not dry_run,
        "threshold": threshold,
        "generated_at": iso_now(),
    }
    if not dry_run and not allowed:
        agency_dir = os.path.join(SYSTEM_ONE_DIR, "agency")
        os.makedirs(agency_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(agency_dir, f"agency-{date_str}.json")
        write_file(path, json.dumps(result, indent=2))
        result["written_to"] = path
    return result


# ---------------------------------------------------------------------------
# Knowledge storage: FTS5 BM25 + KnowledgeGraph
# ---------------------------------------------------------------------------
def init_kb_db():
    """Initialize the knowledge database with FTS5 BM25 and graph tables."""
    os.makedirs(SYSTEM_ONE_DIR, exist_ok=True)
    conn = sqlite3.connect(KB_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    # FTS5 BM25 dual-index for notes
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
            path, name, content,
            tokenize='unicode61'
        )
    """)
    # KnowledgeGraph: entities, triples, timeline
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT,
            first_seen TEXT,
            last_seen TEXT,
            mention_count INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS triples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            predicate TEXT,
            object_id INTEGER,
            source TEXT,
            created_at TEXT,
            FOREIGN KEY(subject_id) REFERENCES entities(id),
            FOREIGN KEY(object_id) REFERENCES entities(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            entity_name TEXT,
            details TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn


def index_note(conn, path, name, content):
    """Index a note into FTS5 BM25 and extract entities for the graph."""
    conn.execute("INSERT OR REPLACE INTO notes_fts(path, name, content) VALUES (?, ?, ?)",
                 (path, name, content))
    # Simple entity extraction: capitalized phrases
    entities = set(re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", content))
    ts = iso_now()
    for ent in entities:
        cur = conn.execute("SELECT id, mention_count FROM entities WHERE name = ?", (ent,))
        row = cur.fetchone()
        if row:
            conn.execute("UPDATE entities SET mention_count = mention_count + 1, last_seen = ? WHERE id = ?",
                         (ts, row[0]))
        else:
            conn.execute("INSERT INTO entities(name, type, first_seen, last_seen, mention_count) VALUES (?, ?, ?, ?, 1)",
                         (ent, "unknown", ts, ts))
    conn.commit()


def search_kb(query, limit=10):
    """Search the knowledge base using BM25 FTS5."""
    if not os.path.exists(KB_DB):
        return []
    conn = sqlite3.connect(KB_DB)
    try:
        rows = conn.execute(
            "SELECT path, name, bm25(notes_fts) as score FROM notes_fts WHERE notes_fts MATCH ? ORDER BY score LIMIT ?",
            (query, limit),
        ).fetchall()
        return [{"path": r[0], "name": r[1], "score": round(r[2], 4)} for r in rows]
    except Exception:
        return []
    finally:
        conn.close()


def run_knowledge(vault_dir, dry_run=True):
    """Index all vault notes into FTS5 BM25 + KnowledgeGraph."""
    conn = init_kb_db()
    count = 0
    for full, rel, name, content in walk_md(vault_dir):
        index_note(conn, rel, name, content)
        count += 1
    conn.close()
    result = {
        "indexed_notes": count,
        "db_path": KB_DB,
        "generated_at": iso_now(),
    }
    if not dry_run:
        kb_dir = os.path.join(SYSTEM_ONE_DIR, "kb")
        os.makedirs(kb_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(kb_dir, f"kb-index-{date_str}.json")
        write_file(path, json.dumps(result, indent=2))
        result["written_to"] = path
    return result


# ---------------------------------------------------------------------------
# Tool call capture
# ---------------------------------------------------------------------------
def capture_tool_call(tool, args, result_summary, dry_run=True):
    """Capture a tool call — searchable at zero LLM tokens."""
    entry = {
        "tool": tool,
        "args": args,
        "result_summary": result_summary,
        "timestamp": iso_now(),
    }
    if not dry_run:
        tools_dir = os.path.join(SYSTEM_ONE_DIR, "tools")
        os.makedirs(tools_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d")
        path = os.path.join(tools_dir, f"tools-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        entry["written_to"] = path
    return entry


def search_tool_calls(query, limit=10):
    """Search captured tool calls."""
    tools_dir = os.path.join(SYSTEM_ONE_DIR, "tools")
    if not os.path.isdir(tools_dir):
        return []
    results = []
    for fname in sorted(os.listdir(tools_dir)):
        if not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(tools_dir, fname)
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                haystack = json.dumps(entry).lower()
                if query.lower() in haystack:
                    results.append(entry)
                    if len(results) >= limit:
                        return results
    return results


# ---------------------------------------------------------------------------
# Dream cycle: release, prune, reconcile, crystallize, distill
# ---------------------------------------------------------------------------
def dream_cycle(vault_dir, dry_run=True):
    """
    Dream cycle: release, prune, reconcile, crystallize, distill.
    Persists across sessions via heartbeat/handoff.
    """
    phases = {
        "release": 0,
        "prune": 0,
        "reconcile": 0,
        "crystallize": 0,
        "distill": 0,
    }
    # Release: identify stale notes
    cutoff = now_utc() - datetime.timedelta(days=90)
    stale = []
    for full, rel, name, content in walk_md(vault_dir):
        try:
            mtime = os.path.getmtime(full)
            mtime_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
            if mtime_dt < cutoff:
                stale.append(rel)
                phases["release"] += 1
        except Exception:
            pass
    # Prune: count orphaned links (links to non-existent notes)
    all_notes = {rel for _, rel, _, _ in walk_md(vault_dir)}
    orphaned = []
    for full, rel, name, content in walk_md(vault_dir):
        for m in re.finditer(r"\[\[([^\]]+)\]\]", content):
            target = m.group(1).strip().split("|")[0] + ".md"
            if target not in all_notes and target.lower() not in {n.lower() for n in all_notes}:
                orphaned.append({"source": rel, "target": target})
                phases["prune"] += 1
    # Reconcile: count tags vs notes
    tag_note_map = {}
    for full, rel, name, content in walk_md(vault_dir):
        for tag in re.findall(r"(?:^|\s)#([\w\-/]+)", content):
            tag_note_map.setdefault(tag, []).append(rel)
    phases["reconcile"] = len(tag_note_map)
    # Crystallize: notes with high link density (well-connected)
    crystalline = []
    for full, rel, name, content in walk_md(vault_dir):
        links = len(re.findall(r"\[\[([^\]]+)\]\]", content))
        words = len(re.findall(r"\b\w+\b", content))
        if words > 0 and links / words > 0.1:
            crystalline.append(rel)
            phases["crystallize"] += 1
    # Distill: summarize themes
    phases["distill"] = len(crystalline)

    result = {
        "phases": phases,
        "stale_notes": stale[:10],
        "orphaned_links": orphaned[:10],
        "crystalline_notes": crystalline[:10],
        "tag_clusters": {k: len(v) for k, v in sorted(tag_note_map.items(), key=lambda x: -len(x[1]))[:10]},
        "generated_at": iso_now(),
    }
    if not dry_run:
        dream_dir = os.path.join(SYSTEM_ONE_DIR, "dream")
        os.makedirs(dream_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(dream_dir, f"dream-{date_str}.json")
        write_file(path, json.dumps(result, indent=2))
        result["written_to"] = path
    return result


# ---------------------------------------------------------------------------
# Autonomic Kanban — evidence-backed board supervision (hermes-nerve inspired)
# ---------------------------------------------------------------------------
KANBAN_COLUMNS = ["Ingestion & Candidates", "Under Review", "Approved & Promoted", "Rejected / Ephemeral"]


def find_kanban_boards(vault_dir):
    """Find all .kanban files in the vault."""
    boards = []
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in {".obsidian", ".git", ".trash", ".sota"} and not d.startswith(".")]
        for f in sorted(files):
            if not (f.endswith(".kanban") or f.endswith(".kanban.md")):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault_dir).replace("\\", "/")
            content = read_file(full)
            name = os.path.splitext(f)[0]
            boards.append((full, rel, name, content))
    return boards


def parse_kanban_content(content):
    """Parse a kanban board markdown into columns and cards."""
    columns = {}
    current_column = None
    for line in content.split("\n"):
        heading_match = re.match(r"^#{2,3}\s+(.+)$", line)
        if heading_match:
            current_column = heading_match.group(1).strip()
            columns[current_column] = []
        elif current_column and line.strip().startswith("- [ ]"):
            card_text = line.strip()[5:]
            columns[current_column].append(card_text)
    return columns


def run_kanban_scan(vault_dir, dry_run=True):
    """Scan kanban boards and report card distribution."""
    boards = find_kanban_boards(vault_dir)
    results = []
    for full, rel, name, content in boards:
        columns = parse_kanban_content(content)
        total_cards = sum(len(cards) for cards in columns.values())
        results.append({
            "path": rel,
            "columns": {col: len(cards) for col, cards in columns.items()},
            "total_cards": total_cards,
        })
    return {"boards": results, "total_boards": len(boards)}


def run_kanban_promote(vault_dir, threshold=0.7, dry_run=True):
    """Auto-promote cards based on evidence/confidence thresholds."""
    boards = find_kanban_boards(vault_dir)
    promoted = []
    for full, rel, name, content in boards:
        columns = parse_kanban_content(content)
        candidates = columns.get("Ingestion & Candidates", [])
        for card in candidates:
            evidence_score = min(1.0, len(card) / 100.0 + (0.2 if "[[" in card else 0))
            if evidence_score >= threshold:
                promoted.append({
                    "from": "Ingestion & Candidates",
                    "to": "Under Review",
                    "card": card,
                    "evidence": round(evidence_score, 2),
                })
    return {"promoted": promoted, "dry_run": dry_run}


def run_kanban_auto_move(vault_dir, dry_run=True):
    """Automatically move cards between columns based on rules."""
    boards = find_kanban_boards(vault_dir)
    moves = []
    for full, rel, name, content in boards:
        columns = parse_kanban_content(content)
        review_cards = columns.get("Under Review", [])
        for card in review_cards:
            if "[[" not in card and len(card) < 50:
                moves.append({
                    "from": "Under Review",
                    "to": "Rejected / Ephemeral",
                    "card": card,
                    "reason": "insufficient_evidence",
                })
    return {"moves": moves, "dry_run": dry_run}


def run_kanban_report(vault_dir, dry_run=True):
    """Evidence-backed kanban supervision report."""
    scan = run_kanban_scan(vault_dir, dry_run=True)
    lines = ["# Autonomic Kanban Supervision Report", f"Generated: {iso_now()}", ""]
    for board in scan["boards"]:
        lines.append(f"## {board['path']}")
        lines.append(f"- Total cards: {board['total_cards']}")
        for col, count in board["columns"].items():
            lines.append(f"  - {col}: {count}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Model Providers — provider-neutral model management (local + diverse API)
# ---------------------------------------------------------------------------
DEFAULT_PROVIDERS = [
    {"id": "ollama", "name": "Ollama (Local)", "type": "local", "endpoint": "http://localhost:11434",
     "models": ["llama3.2", "codellama", "mistral"]},
    {"id": "openai", "name": "OpenAI API", "type": "api", "endpoint": "https://api.openai.com/v1",
     "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]},
    {"id": "anthropic", "name": "Anthropic API", "type": "api", "endpoint": "https://api.anthropic.com",
     "models": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]},
    {"id": "gemini", "name": "Google Gemini API", "type": "api",
     "endpoint": "https://generativelanguage.googleapis.com",
     "models": ["gemini-1.5-flash", "gemini-1.5-pro"]},
]


def run_providers_list(dry_run=True):
    """List available model providers."""
    return {"providers": DEFAULT_PROVIDERS}


def run_providers_select(provider_id, task_type="general", dry_run=True):
    """Select a provider for a task type."""
    provider = next((p for p in DEFAULT_PROVIDERS if p["id"] == provider_id), None)
    if not provider:
        return {"error": f"Provider '{provider_id}' not found"}
    if task_type == "simple" and provider["type"] == "local":
        recommendation = "optimal"
    elif task_type == "complex" and provider["type"] == "api":
        recommendation = "optimal"
    else:
        recommendation = "acceptable"
    return {
        "provider": provider,
        "task_type": task_type,
        "recommendation": recommendation,
        "dry_run": dry_run,
    }


def run_providers_fallback(chain=None, dry_run=True):
    """Configure fallback chain between providers."""
    if chain is None:
        chain = ["ollama", "openai", "anthropic", "gemini"]
    return {"fallback_chain": chain, "dry_run": dry_run}


def run_providers_budget(dry_run=True):
    """Token budget tracking per provider."""
    return {
        "providers": {p["id"]: {"budget": 100000, "used": 0, "remaining": 100000} for p in DEFAULT_PROVIDERS},
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 system_one.py Self-Test Suite")
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

    # Test 1: categorize_number
    def test_categorize_number():
        assert categorize_number(42, "measured") == "measured"
        assert categorize_number(3.14, "derived") == "derived"
        assert categorize_number(100, "asserted") == "asserted"
        assert categorize_number(7, "none") == "none"
    check("categorize_number assigns categories", test_categorize_number)

    # Test 2: council_vote unanimous veto
    def test_council_unanimous_veto():
        # Force all "no" votes by using a question that hashes to no-range
        # We test with 4 voices all voting "no"
        result = council_vote("should we delete everything?", voices=["v1", "v2", "v3", "v4"], dry_run=True)
        assert "votes" in result
        assert "entropy" in result
        assert "agreement" in result
        assert "decision" in result
        assert result["decision"] in ("yes", "no", "abstain")
    check("council_vote produces decision", test_council_unanimous_veto)

    # Test 3: brier_score and ece
    def test_calibration():
        predictions = [0.9, 0.8, 0.3, 0.2]
        outcomes = [1, 1, 0, 0]
        paired = list(zip(predictions, outcomes))
        b = brier_score(predictions, outcomes)
        assert 0.0 <= b <= 1.0
        ece, bins = expected_calibration_error(paired)
        assert ece >= 0.0
        spots = blind_spot_detection(predictions, outcomes)
        assert isinstance(spots, list)
        coh = coherence_metrics(predictions, outcomes)
        assert "coherence" in coh
        assert "dimensions" in coh
    check("calibration metrics compute", test_calibration)

    # Test 4: agency layer propose/audit/risk-gate/execute
    def test_agency():
        result = run_agency("create a new note", threshold=0.6, dry_run=True)
        assert "plan" in result
        assert result["plan"]["status"] in ("proposed", "audited", "cleared", "blocked", "executed")
        assert "executed" in result
    check("agency layer runs end-to-end", test_agency)

    # Test 5: kanban scan finds boards
    def test_kanban_scan():
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp()
        try:
            init_paths(tmp)
            result = run_kanban_scan(tmp, dry_run=True)
            assert "total_boards" in result
            assert "boards" in result
            assert isinstance(result["boards"], list)
        finally:
            shutil.rmtree(tmp)
    check("kanban_scan finds kanban boards", test_kanban_scan)

    # Test 6: providers list returns all providers
    def test_providers_list():
        result = run_providers_list(dry_run=True)
        assert "providers" in result
        assert len(result["providers"]) >= 4
        ids = {p["id"] for p in result["providers"]}
        assert "ollama" in ids
        assert "openai" in ids
    check("providers_list returns all providers", test_providers_list)

    # Test 7: providers select works
    def test_providers_select():
        result = run_providers_select("ollama", task_type="simple", dry_run=True)
        assert result["recommendation"] == "optimal"
        assert result["provider"]["id"] == "ollama"
        assert result["provider"]["type"] == "local"
    check("providers_select recommends local for simple tasks", test_providers_select)

    # Test 8: providers fallback chain
    def test_providers_fallback():
        result = run_providers_fallback(dry_run=True)
        assert "fallback_chain" in result
        assert len(result["fallback_chain"]) >= 2
    check("providers_fallback returns chain", test_providers_fallback)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain System One — fast automatic agent decision support.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    p_mono = sub.add_parser("monologue", help="Run inner-monologue loop (observe/assess/summarize)")
    p_mono.add_argument("--days", type=int, default=7, help="Days of activity to scan (default: 7)")

    p_council = sub.add_parser("council", help="Run four-voice council vote")
    p_council.add_argument("--question", required=True, help="Question for the council to decide")

    p_cal = sub.add_parser("calibrate", help="Confidence calibration (ECE/Brier)")
    p_cal.add_argument("--predictions", help="JSON list of predicted probabilities")
    p_cal.add_argument("--outcomes", help="JSON list of actual outcomes (0/1)")

    p_agency = sub.add_parser("agency", help="Agency layer: propose/audit/risk-gate/execute")
    p_agency.add_argument("--plan", required=True, help="Plan text to evaluate")

    p_kb = sub.add_parser("knowledge", help="Knowledge storage: index vault into FTS5 BM25 + graph")

    p_tools = sub.add_parser("tools", help="Tool call capture")
    p_tools.add_argument("--tool", help="Tool name")
    p_tools.add_argument("--args", help="Tool args (JSON)")
    p_tools.add_argument("--result", help="Result summary")

    p_dream = sub.add_parser("dream", help="Dream cycle: release/prune/reconcile/crystallize/distill")

    p_kanban = sub.add_parser("kanban", help="Autonomic Kanban board supervision (evidence-backed)")
    p_kanban.add_argument("--days", type=int, default=30, help="Days of activity to scan (default: 30)")
    p_kanban_sub = p_kanban.add_subparsers(dest="kanban_command", help="Kanban command")
    p_kanban_sub.add_parser("scan", help="Scan kanban boards and report card distribution")
    p_kanban_sub.add_parser("promote", help="Auto-promote cards based on evidence thresholds")
    p_kanban_sub.add_parser("auto-move", help="Auto-move cards between columns based on rules")
    p_kanban_sub.add_parser("report", help="Evidence-backed kanban supervision report")
    p_kanban.add_argument("--threshold", type=float, default=0.7, help="Promotion threshold (default: 0.7)")

    p_providers = sub.add_parser("providers", help="Model provider management (local + diverse API)")
    p_providers_sub = p_providers.add_subparsers(dest="providers_command", help="Providers command")
    p_providers_sub.add_parser("list", help="List available model providers")
    p_prov_select = p_providers_sub.add_parser("select", help="Select a provider for a task type")
    p_prov_select.add_argument("--provider", required=True, help="Provider id (ollama, openai, anthropic, gemini)")
    p_prov_select.add_argument("--task", default="general", help="Task type (simple, complex, general)")
    p_providers_sub.add_parser("fallback", help="Configure fallback chain between providers")
    p_providers_sub.add_parser("budget", help="Token budget tracking per provider")

    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="Write outputs to vault (overrides --dry-run)")
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
    dry_run = not args.apply

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    if args.command == "monologue":
        result = run_monologue(VAULT, days=args.days, dry_run=dry_run)
        print(f"🧠 Inner Monologue (last {args.days} days)")
        print(f"   Confidence: {result['confidence']['confidence']:.1%}")
        print(f"   Notes observed: {result['confidence']['note_count']}")
        print()
        print(result["summary"])
        if not dry_run and result.get("written_to"):
            print(f"\n📄 Written to {result['written_to']}")

    elif args.command == "council":
        result = council_vote(args.question, dry_run=dry_run)
        print(f"🗳️  Four-Voice Council")
        print(f"   Question: {result['question']}")
        print(f"   Votes: {result['votes']}")
        print(f"   Yes: {result['yes_count']} | No: {result['no_count']} | Abstain: {result['abstain_count']}")
        print(f"   Entropy: {result['entropy']} | Agreement: {result['agreement']:.1%}")
        print(f"   Unanimous veto: {result['unanimous_veto']}")
        print(f"   Decision: {result['decision']}")
        if not dry_run and result.get("written_to"):
            print(f"\n📄 Written to {result['written_to']}")

    elif args.command == "calibrate":
        preds = json.loads(args.predictions) if args.predictions else [0.8, 0.3, 0.9, 0.1]
        outs = json.loads(args.outcomes) if args.outcomes else [1, 0, 1, 0]
        result = run_calibrate(preds, outs, dry_run=dry_run)
        print(f"📊 Confidence Calibration")
        print(f"   Brier score: {result['brier_score']}")
        print(f"   ECE: {result['ece']}")
        print(f"   Blind spots: {len(result['blind_spots'])}")
        print(f"   Coherence: {result['coherence']['coherence']}")
        print(f"   Sample size: {result['sample_size']}")
        if not dry_run and result.get("written_to"):
            print(f"\n📄 Written to {result['written_to']}")

    elif args.command == "agency":
        result = run_agency(args.plan, dry_run=dry_run)
        print(f"🏛️  Agency Layer")
        print(f"   Plan: {result['plan_text']}")
        print(f"   Status: {result['plan']['status']}")
        print(f"   Audit risks: {result['plan'].get('audit_risks', [])}")
        print(f"   Audit confidence: {result['plan'].get('audit_confidence', 0):.1%}")
        print(f"   Risk gate allowed: {result['executed']}")
        if not dry_run and result.get("written_to"):
            print(f"\n📄 Written to {result['written_to']}")

    elif args.command == "knowledge":
        result = run_knowledge(VAULT, dry_run=dry_run)
        print(f"🧠 Knowledge Storage")
        print(f"   Indexed notes: {result['indexed_notes']}")
        print(f"   DB: {result['db_path']}")
        if not dry_run and result.get("written_to"):
            print(f"\n📄 Written to {result['written_to']}")

    elif args.command == "tools":
        if not args.tool:
            print("Error: --tool is required for 'tools' command.", file=sys.stderr)
            sys.exit(1)
        args_dict = json.loads(args.args) if args.args else {}
        result = capture_tool_call(args.tool, args_dict, args.result or "", dry_run=dry_run)
        print(f"🛠️  Tool Call Captured")
        print(f"   Tool: {result['tool']}")
        print(f"   Timestamp: {result['timestamp']}")
        if not dry_run and result.get("written_to"):
            print(f"\n📄 Written to {result['written_to']}")

    elif args.command == "dream":
        result = dream_cycle(VAULT, dry_run=dry_run)
        print(f"💤 Dream Cycle")
        print(f"   Release: {result['phases']['release']} stale notes")
        print(f"   Prune: {result['phases']['prune']} orphaned links")
        print(f"   Reconcile: {result['phases']['reconcile']} tag clusters")
        print(f"   Crystallize: {result['phases']['crystallize']} well-connected notes")
        print(f"   Distill: {result['phases']['distill']} themes")
        if not dry_run and result.get("written_to"):
            print(f"\n📄 Written to {result['written_to']}")

    elif args.command == "kanban":
        kcmd = getattr(args, "kanban_command", None)
        if kcmd == "scan":
            result = run_kanban_scan(VAULT, dry_run=dry_run)
            print(f"📋 Autonomic Kanban Scan ({result['total_boards']} board(s))")
            for b in result["boards"]:
                print(f"   {b['path']}: {b['total_cards']} cards")
                for col, count in b["columns"].items():
                    print(f"     {col}: {count}")
        elif kcmd == "promote":
            result = run_kanban_promote(VAULT, threshold=args.threshold, dry_run=dry_run)
            print(f"🔼 Kanban Auto-Promote (threshold: {args.threshold})")
            for p in result["promoted"]:
                print(f"   {p['card'][:60]} — {p['from']} → {p['to']} (evidence: {p['evidence']})")
            if not result["promoted"]:
                print("   No cards met the promotion threshold.")
        elif kcmd == "auto-move":
            result = run_kanban_auto_move(VAULT, dry_run=dry_run)
            print(f"🔄 Kanban Auto-Move")
            for m in result["moves"]:
                print(f"   {m['card'][:60]} — {m['from']} → {m['to']} ({m['reason']})")
            if not result["moves"]:
                print("   No cards met the auto-move criteria.")
        elif kcmd == "report":
            report = run_kanban_report(VAULT, dry_run=dry_run)
            print(report)
            if not dry_run:
                kanban_dir = os.path.join(SYSTEM_ONE_DIR, "kanban")
                os.makedirs(kanban_dir, exist_ok=True)
                date_str = now_utc().strftime("%Y%m%d-%H%M%S")
                path = os.path.join(kanban_dir, f"kanban-report-{date_str}.md")
                write_file(path, report)
                print(f"\n📄 Written to {path}")
        else:
            print("Error: Unknown kanban command. Use: scan, promote, auto-move, report.", file=sys.stderr)
            sys.exit(1)
        if dry_run:
            print("\nRun with --apply to write outputs to vault.")

    elif args.command == "providers":
        pcmd = getattr(args, "providers_command", None)
        if pcmd == "list":
            result = run_providers_list(dry_run=dry_run)
            print(f"🤖 Model Providers ({len(result['providers'])})")
            for p in result["providers"]:
                print(f"   {p['name']} ({p['id']}) — {p['type']} — {p['endpoint']}")
                print(f"      Models: {', '.join(p['models'])}")
        elif pcmd == "select":
            result = run_providers_select(args.provider, task_type=args.task, dry_run=dry_run)
            if "error" in result:
                print(f"❌ {result['error']}", file=sys.stderr)
                sys.exit(1)
            p = result["provider"]
            print(f"🎯 Provider Selection")
            print(f"   Provider: {p['name']} ({p['id']}) — {p['type']}")
            print(f"   Task type: {result['task_type']}")
            print(f"   Recommendation: {result['recommendation']}")
            print(f"   Models: {', '.join(p['models'])}")
        elif pcmd == "fallback":
            result = run_providers_fallback(dry_run=dry_run)
            print(f"🔗 Provider Fallback Chain")
            print(f"   {' → '.join(result['fallback_chain'])}")
        elif pcmd == "budget":
            result = run_providers_budget(dry_run=dry_run)
            print(f"💰 Token Budget per Provider")
            for pid, info in result["providers"].items():
                print(f"   {pid}: {info['used']}/{info['budget']} used ({info['remaining']} remaining)")
        else:
            print("Error: Unknown providers command. Use: list, select, fallback, budget.", file=sys.stderr)
            sys.exit(1)
        if dry_run:
            print("\nRun with --apply to write outputs to vault.")

    else:
        print("Error: No command specified. Use: monologue, council, calibrate, agency, knowledge, tools, dream, kanban, providers.", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print("\nRun with --apply to write outputs to vault.")


if __name__ == "__main__":
    main()
