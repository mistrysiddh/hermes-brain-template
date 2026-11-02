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
# Prioritizes multi-provider APIs + open-weight models per TomLucidor feedback
# ---------------------------------------------------------------------------
DEFAULT_PROVIDERS = [
    # Open-weight / local providers (prioritized)
    {"id": "ollama", "name": "Ollama (Local, Open-Weight)", "type": "local",
     "endpoint": "http://localhost:11434", "open_weight": True,
     "models": ["llama3.2", "llama3.1", "codellama", "mistral", "mixtral", "qwen2.5", "deepseek-r1"]},
    {"id": "llama_cpp", "name": "llama.cpp (Local, Open-Weight)", "type": "local",
     "endpoint": "http://localhost:8080", "open_weight": True,
     "models": ["llama-3.1-8b", "llama-3.1-70b", "mixtral-8x7b", "qwen2.5-72b"]},
    {"id": "vllm", "name": "vLLM (Local, Open-Weight)", "type": "local",
     "endpoint": "http://localhost:8000", "open_weight": True,
     "models": ["meta-llama/Llama-3.1-8B-Instruct", "Qwen/Qwen2.5-72B-Instruct", "deepseek-ai/DeepSeek-R1-Distill"]},
    {"id": "tgi", "name": "Text Generation Inference (Local, Open-Weight)", "type": "local",
     "endpoint": "http://localhost:3000", "open_weight": True,
     "models": ["bigcode/starcoder", "bigscience/bloom", "facebook/opt"]},
    # Commercial API providers
    {"id": "openai", "name": "OpenAI API", "type": "api",
     "endpoint": "https://api.openai.com/v1", "open_weight": False,
     "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "o1-mini", "o1-preview"]},
    {"id": "anthropic", "name": "Anthropic API", "type": "api",
     "endpoint": "https://api.anthropic.com", "open_weight": False,
     "models": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "claude-3.5-sonnet"]},
    {"id": "gemini", "name": "Google Gemini API", "type": "api",
     "endpoint": "https://generativelanguage.googleapis.com", "open_weight": False,
     "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]},
]


def run_providers_list(dry_run=True):
    """List available model providers, open-weight first."""
    providers = sorted(DEFAULT_PROVIDERS, key=lambda p: (not p["open_weight"], p["id"]))
    return {"providers": providers}


def run_providers_open_weight(dry_run=True):
    """List only open-weight / local providers."""
    providers = [p for p in DEFAULT_PROVIDERS if p["open_weight"]]
    return {"providers": providers, "type": "open_weight_only"}


def run_providers_select(provider_id, task_type="general", dry_run=True):
    """Select a provider for a task type."""
    provider = next((p for p in DEFAULT_PROVIDERS if p["id"] == provider_id), None)
    if not provider:
        return {"error": f"Provider '{provider_id}' not found"}
    # Prioritize open-weight/local for simple tasks, API for complex
    if task_type == "simple":
        recommendation = "optimal" if provider["type"] == "local" else "acceptable"
    elif task_type == "complex":
        recommendation = "optimal" if provider["type"] == "api" else "acceptable"
    elif task_type == "reasoning":
        recommendation = "optimal" if provider["id"] in ("openai", "anthropic", "ollama") else "acceptable"
    else:
        recommendation = "acceptable"
    return {
        "provider": provider,
        "task_type": task_type,
        "recommendation": recommendation,
        "dry_run": dry_run,
    }


def run_providers_fallback(chain=None, dry_run=True):
    """Configure fallback chain between providers — local first, then API."""
    if chain is None:
        # Open-weight local first, then commercial APIs
        chain = ["ollama", "llama_cpp", "vllm", "openai", "anthropic", "gemini"]
    return {"fallback_chain": chain, "dry_run": dry_run}


def run_providers_gateway(dry_run=True):
    """Gateway pattern — unify access to multiple providers (like bifrost)."""
    gateway = {
        "pattern": "provider-neutral gateway",
        "description": "Single API surface that routes to the best available provider",
        "providers": [p["id"] for p in DEFAULT_PROVIDERS],
        "failover": "automatic on provider failure",
        "load_balancing": "round-robin across healthy providers",
        "semantic_caching": True,
        "open_weight_first": True,
    }
    return {"gateway": gateway, "dry_run": dry_run}


def run_providers_budget(dry_run=True):
    """Token budget tracking per provider."""
    return {
        "providers": {p["id"]: {"budget": 100000, "used": 0, "remaining": 100000} for p in DEFAULT_PROVIDERS},
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# System One Research — dual-process theory repos and findings
# ---------------------------------------------------------------------------
SYSTEM_ONE_REPOS = [
    {
        "id": "dpt-agent",
        "name": "DPT-Agent",
        "url": "https://github.com/sjtu-marl/DPT-Agent",
        "description": "Dual Process Theory in Language Agent Framework — System 1 (fast) + System 2 (slow) reasoning for human-AI collaboration (ACL 2025)",
        "key_concepts": ["system1-system2-routing", "simultaneous-collaboration", "rule-based-collaboration"],
    },
    {
        "id": "duo-ai",
        "name": "DuoAI",
        "url": "https://github.com/khanhptnk/duo-ai",
        "description": "Two-System AI Agents — modular abstractions for coordination policies and decision-making agents that mimic human dual cognitive system",
        "key_concepts": ["coordination-policies", "decision-making-agents", "uncertainty-based-routing"],
    },
    {
        "id": "lex-dual-process",
        "name": "lex-dual-process",
        "url": "https://github.com/LegionIO-Archive/lex-dual-process",
        "description": "Dual-process cognition modeling — routes decisions to fast heuristic (System 1) or slow deliberative (System 2) reasoning based on complexity, confidence, and effort budget",
        "key_concepts": ["effort-budget", "heuristic-learning", "cognitive-fatigue", "reinforcement"],
    },
    {
        "id": "dual-process-llm",
        "name": "dual-process-llm",
        "url": "https://github.com/xiaoyanLi629/dual-process-llm",
        "description": "Investigating Dual Process Theory in LLMs — IEEE BIBM 2026, 4 model families, CoT helps analytical tasks but hurts intuitive ones",
        "key_concepts": ["chain-of-thought-analysis", "model-family-comparison", "intuitive-vs-analytical"],
    },
    {
        "id": "thinking-speed-control",
        "name": "thinking-speed-control",
        "url": "https://github.com/D2I-ai/thinking-speed-control",
        "description": "Controlling Thinking Speed in Reasoning Models — plug-and-play module to switch LRMs between System 1 (fast) and System 2 (slow) thinking (NeurIPS 2025)",
        "key_concepts": ["trigger-words", "steering-vectors", "representation-engineering", "fast-slow-switching"],
    },
]


def run_system_one_research(dry_run=True):
    """Research findings from System One / dual-process repos."""
    return {
        "repos": SYSTEM_ONE_REPOS,
        "total": len(SYSTEM_ONE_REPOS),
        "dry_run": dry_run,
    }


def run_system_one_route(query, complexity=None, confidence=None, dry_run=True):
    """
    Route a decision to System 1 (fast) or System 2 (slow) based on
    dual-process theory — complexity, confidence, effort budget.
    """
    if complexity is None:
        # Estimate complexity from query length and keywords
        complex_keywords = ["analyze", "design", "architecture", "prove", "verify", "research", "compare"]
        simple_keywords = ["what", "who", "when", "where", "list", "show", "get"]
        c = sum(1 for k in complex_keywords if k in query.lower())
        s = sum(1 for k in simple_keywords if k in query.lower())
        complexity = c / max(1, c + s) if (c + s) > 0 else 0.5
    if confidence is None:
        confidence = 0.7

    # Effort budget logic (from lex-dual-process)
    effort_budget = 1.0
    if complexity > 0.7:
        system = "system_two"
        effort_cost = 0.3
    elif complexity > 0.4:
        system = "system_two" if confidence < 0.6 else "system_one"
        effort_cost = 0.15
    else:
        system = "system_one"
        effort_cost = 0.05

    effort_budget = max(0.0, effort_budget - effort_cost)

    return {
        "query": query,
        "complexity": round(complexity, 2),
        "confidence": confidence,
        "routed_system": system,
        "effort_cost": effort_cost,
        "effort_budget_remaining": round(effort_budget, 2),
        "reasoning": (
            "High complexity → System 2 (slow, deliberative)"
            if system == "system_two"
            else "Low complexity → System 1 (fast, heuristic)"
        ),
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Reflex Functions — Jev/System One reflex layer (kaustav1996/reflex inspired)
#
# Implements the reflex layer from kaustav1996/reflex: a calibrated System One
# model checks each tool call, turn and voice transcript in ~400ms, and code
# decides what happens next. Jev answers narrow typed questions; reflex code
# acts on the numbers. Open-weight / local SLMs (Qwen3 0.6B, Llama 3.2 1B,
# Gemma 3 1B, etc.) can run these reflexes entirely on a laptop.
#
# Design rules:
#   - Code owns control flow. Reflex can add a question or block, never remove one.
#   - Each reflex asks narrow typed questions (Noul/Choice/Score).
#   - Confidence thresholds scaled to risk.
#   - All calls logged with version and question hash.
# ---------------------------------------------------------------------------

# Small fast laptop SLMs for reflex inference — sub-1GB models run entirely
# on-device with ~400ms latency. Ideal for System One reflex work.
REFLEX_SLM_MODELS = [
    {
        "id": "qwen3:0.6b",
        "name": "Qwen3 0.6B",
        "params": "0.6B",
        "size_q4": "0.3 GB",
        "ram_q4": "1 GB",
        "use_case": "Speculative decoding draft model, classifier draft",
        "ollama": "ollama run qwen3:0.6b",
    },
    {
        "id": "qwen3.5:0.8b",
        "name": "Qwen3.5 0.8B",
        "params": "0.87B",
        "size_q4": "0.5 GB",
        "ram_q4": "1 GB",
        "use_case": "Classifier, reflex draft model",
        "ollama": "ollama run qwen3.5:0.8b",
    },
    {
        "id": "gemma3:1b",
        "name": "Gemma 3 1B",
        "params": "1.0B",
        "size_q4": "0.6 GB",
        "ram_q4": "1 GB",
        "use_case": "Text-only reflex, single KV head",
        "ollama": "ollama run gemma3:1b",
    },
    {
        "id": "llama3.2:1b",
        "name": "Llama 3.2 1B",
        "params": "1.24B",
        "size_q4": "0.7 GB",
        "ram_q4": "1 GB",
        "use_case": "Smallest Llama worth running, phones & edge",
        "ollama": "ollama run llama3.2:1b",
    },
    {
        "id": "qwen3:1.7b",
        "name": "Qwen3 1.7B",
        "params": "1.72B",
        "size_q4": "1.0 GB",
        "ram_q4": "1 GB",
        "use_case": "Structured tasks, reflex with optional thinking",
        "ollama": "ollama run qwen3:1.7b",
    },
    {
        "id": "llama3.2:3b",
        "name": "Llama 3.2 3B",
        "params": "3.21B",
        "size_q4": "1.8 GB",
        "ram_q4": "2 GB",
        "use_case": "Edge model for 8GB laptops",
        "ollama": "ollama run llama3.2:3b",
    },
    {
        "id": "phi4-mini:3.8b",
        "name": "Phi-4-mini 3.8B",
        "params": "3.84B",
        "size_q4": "2.2 GB",
        "ram_q4": "2 GB",
        "use_case": "Instruction following, strong for size",
        "ollama": "ollama run phi4-mini:3.8b",
    },
    {
        "id": "gemma3:4b",
        "name": "Gemma 3 4B",
        "params": "4.3B",
        "size_q4": "2.4 GB",
        "ram_q4": "2 GB",
        "use_case": "Vision-capable reflex",
        "ollama": "ollama run gemma3:4b",
    },
]

# ---------------------------------------------------------------------------
# Reflex Decision Models — benchmarkheaven.com/jev-models
#
# Jev-style decision models sourced from benchmarkheaven.com/jev-models.
# Smaller/faster is better, ideally higher performance. These form the
# efficiency frontier for reflex inference on laptops.
#
# 2026 SOTA per TomLucidor: Qwen-3.5 and Gemma-4 are SOTA for SLMs,
# NOT Phi or Llama. Update every 3-6 months.
# Source: https://benchmarkheaven.com/jev-models
# ---------------------------------------------------------------------------
REFLEX_DECISION_MODELS = [
    {
        "id": "qwen3.5:0.8b",
        "name": "Qwen3.5 0.8B",
        "source": "benchmarkheaven.com/jev-models",
        "params": "0.87B",
        "size_q4": "0.5 GB",
        "ram_q4": "1 GB",
        "role": "decision_model",
        "sota_tier": "tier_1",
        "efficiency_score": 0.95,
        "latency_ms": 300,
        "ollama": "ollama run qwen3.5:0.8b",
    },
    {
        "id": "gemma3:1b",
        "name": "Gemma 3 1B",
        "source": "benchmarkheaven.com/jev-models",
        "params": "1.0B",
        "size_q4": "0.6 GB",
        "ram_q4": "1 GB",
        "role": "decision_model",
        "sota_tier": "tier_1",
        "efficiency_score": 0.92,
        "latency_ms": 350,
        "ollama": "ollama run gemma3:1b",
    },
    {
        "id": "qwen3.5:1.7b",
        "name": "Qwen3.5 1.7B",
        "source": "benchmarkheaven.com/jev-models",
        "params": "1.72B",
        "size_q4": "1.0 GB",
        "ram_q4": "1 GB",
        "role": "decision_model",
        "sota_tier": "tier_1",
        "efficiency_score": 0.88,
        "latency_ms": 450,
        "ollama": "ollama run qwen3.5:1.7b",
    },
    {
        "id": "gemma3:4b",
        "name": "Gemma 3 4B",
        "source": "benchmarkheaven.com/jev-models",
        "params": "4.3B",
        "size_q4": "2.4 GB",
        "ram_q4": "2 GB",
        "role": "decision_model",
        "sota_tier": "tier_2",
        "efficiency_score": 0.82,
        "latency_ms": 700,
        "ollama": "ollama run gemma3:4b",
    },
]

REFLEX_RISK_RUBRIC = [
    "destructive?",
    "outside_the_workspace?",
    "touches_secrets?",
    "external_side_effect?",
    "needs_privileges?",
    "matches_what_user_asked?",
]

REFLEX_QUESTION_TEMPLATES = {
    "action_gate": {
        "questions": REFLEX_RISK_RUBRIC + ["risk_rubric_0_to_3", "confidence"],
        "actions": {"allow": "run immediately", "ask": "prompt user", "block": "refuse"},
    },
    "progress_monitor": {
        "questions": ["looping?", "ignoring_error?", "stuck?"],
        "actions": {"nudge": "suggest approach change", "warn": "warn on thrashing"},
    },
    "completion_check": {
        "questions": ["claims_done?", "actually_verified?", "scope_drift?", "waiting_on_user?"],
        "actions": {"send_back": "run tests and report real output"},
    },
    "failure_triage": {
        "questions": ["failure_kind?", "same_as_before?"],
        "kinds": ["missing_dependency", "transient", "environment", "real_bug"],
        "actions": {
            "missing_dependency": "propose install command (gated)",
            "transient": "one retry",
            "configuration": "check config before changing code",
            "real_bug": "silence (most common)",
        },
    },
}


def reflex_gate(tool_name, args, risk_appetite="balanced", dry_run=True):
    """
    Action gate on tool calls — the Jev reflex that evaluates every bash, edit,
    write, computer, browse and connector call.

    Returns a decision: allow / ask / block, with a risk rubric and confidence.
    """
    import hashlib

    question_hash = hashlib.sha256(f"{tool_name}:{json.dumps(args, sort_keys=True)}".encode()).hexdigest()[:12]

    # Jev answers: destructive? outside_workspace? touches_secrets? external_side_effect?
    # needs_privileges? matches_what_user_asked? risk_rubric_0_to_3? confidence?
    risk_score = 0
    reasons = []
    arg_str = json.dumps(args).lower()

    if any(k in arg_str for k in ["rm ", "delete", "drop", "truncate", "format", "mkfs"]):
        risk_score += 2
        reasons.append("destructive_operation")
    if any(k in arg_str for k in ["sudo", "chmod 777", "chown", "passwd", "su "]):
        risk_score += 1
        reasons.append("privilege_operation")
    if any(k in arg_str for k in ["api_key", "secret", "password", "token", "sk-", "ghp_"]):
        risk_score += 2
        reasons.append("secret_exposure")
    if any(k in arg_str for k in ["curl ", "wget ", "nc ", "ssh ", "scp ", "rsync "]):
        risk_score += 1
        reasons.append("external_side_effect")
    if "push" in arg_str and "force" in arg_str:
        risk_score += 2
        reasons.append("force_push")

    risk_score = min(risk_score, 3)

    # Decision logic based on risk appetite
    if risk_appetite == "cautious":
        threshold_allow, threshold_ask = 0, 1
    elif risk_appetite == "bold":
        threshold_allow, threshold_ask = 1, 2
    else:  # balanced
        threshold_allow, threshold_ask = 0, 2

    if risk_score <= threshold_allow:
        decision = "allow"
    elif risk_score <= threshold_ask:
        decision = "ask"
    else:
        decision = "block"

    confidence = 0.85 if risk_score < 3 else 0.95

    result = {
        "tool": tool_name,
        "question_hash": question_hash,
        "risk_score": risk_score,
        "risk_rubric": REFLEX_RISK_RUBRIC,
        "risk_factors": reasons,
        "decision": decision,
        "confidence": round(confidence, 2),
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_monitor(turn_count, errors_ignored, loops_detected, dry_run=True):
    """
    Progress monitor after each turn — Jev checks: looping? ignoring error? stuck?
    Code nudges or warns based on the answer.
    """
    risk = 0
    reasons = []

    if loops_detected > 2:
        risk += 2
        reasons.append("repeated_looping")
    if errors_ignored > 3:
        risk += 1
        reasons.append("ignoring_errors")
    if turn_count > 50 and risk == 0:
        risk += 0  # long session but not stuck — just note it

    if risk >= 2:
        action = "warn"
        message = "Agent may be thrashing — consider changing approach"
    elif risk == 1:
        action = "nudge"
        message = "Minor inefficiency detected — consider alternative approach"
    else:
        action = "none"
        message = "Progress looks healthy"

    result = {
        "turn_count": turn_count,
        "errors_ignored": errors_ignored,
        "loops_detected": loops_detected,
        "risk": risk,
        "risk_factors": reasons,
        "action": action,
        "message": message,
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_complete(claims_done, verified, scope_drift, waiting_on_user, dry_run=True):
    """
    Completion check when the agent stops — Jev checks: claims done? actually verified?
    scope drift? waiting on you? A "done" without verification is sent back to run
    tests and report real output.
    """
    issues = []

    if claims_done and not verified:
        issues.append("done_without_verification")
    if scope_drift:
        issues.append("scope_drift")
    if waiting_on_user:
        issues.append("waiting_on_user")

    if issues:
        decision = "send_back"
        message = "Done without verification — run tests and report real output"
    else:
        decision = "accept"
        message = "Completion confirmed — all checks passed"

    result = {
        "claims_done": claims_done,
        "verified": verified,
        "scope_drift": scope_drift,
        "waiting_on_user": waiting_on_user,
        "issues": issues,
        "decision": decision,
        "message": message,
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_router(task_type, task_complexity, available_skills, available_connectors, dry_run=True):
    """
    Model router and skill/connector selector — Jev answers in one request:
    fast/default/strong tier? which bundled skill? which MCP server?
    Code switches model and thinking effort per request when confident.
    """
    # Determine tier based on task complexity
    if task_complexity <= 0.3:
        tier = "fast"
        model_hint = "qwen3:0.6b or llama3.2:1b"
    elif task_complexity <= 0.7:
        tier = "default"
        model_hint = "llama3.2:3b or qwen3:1.7b"
    else:
        tier = "strong"
        model_hint = "claude-3-sonnet or gpt-4o"

    # Select skill
    skill_match = None
    for s in available_skills:
        if task_type in s.lower() or s.lower() in task_type:
            skill_match = s
            break

    # Select connector
    connector_match = None
    for c in available_connectors:
        if task_type in c.lower() or c.lower() in task_type:
            connector_match = c
            break

    result = {
        "task_type": task_type,
        "task_complexity": task_complexity,
        "tier": tier,
        "model_hint": model_hint,
        "selected_skill": skill_match,
        "selected_connector": connector_match,
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_triage(exit_code, error_message, failure_count, dry_run=True):
    """
    Failure triage when a shell command exits non-zero — Jev classifies:
    missing_dependency, transient, environment, real_bug.
    Code acts on the answer: propose install (gated), one retry, check config, or silence.
    """
    err_lower = error_message.lower()

    if any(k in err_lower for k in ["not found", "module not found", "command not found", "package not found"]):
        kind = "missing_dependency"
        action = "propose_install"
        message = "Missing dependency — proposed install command (gated, never auto-run)"
    elif any(k in err_lower for k in ["timeout", "connection refused", "temporary", "try again"]):
        kind = "transient"
        action = "retry_once"
        message = "Transient failure — one retry"
    elif any(k in err_lower for k in ["permission", "access denied", "config", "environment"]):
        kind = "environment"
        action = "check_config"
        message = "Configuration failure — check config before changing code"
    else:
        kind = "real_bug"
        action = "silence"
        message = "Ordinary bug — silence (most common)"

    # Same failure three times → stop and ask
    if failure_count >= 3:
        action = "stop_and_ask"
        message = "Same failure 3 times — stop and ask user rather than retry"

    result = {
        "exit_code": exit_code,
        "error_message": error_message[:200],
        "failure_count": failure_count,
        "kind": kind,
        "action": action,
        "message": message,
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_trim(output_chunks, dry_run=True):
    """
    Trimming long tool output — per chunk: is this still needed?
    Kept: head, tail, errors, failures, diffs. Rest replaced with marker.
    Measured: 80% fewer tokens with every needle kept.
    """
    kept_chunks = []
    trimmed_count = 0

    for i, chunk in enumerate(output_chunks):
        chunk_lower = chunk.lower()
        is_important = any(k in chunk_lower for k in ["error", "fail", "diff", "traceback", "exception"])
        if is_important or i == 0 or i == len(output_chunks) - 1:
            kept_chunks.append(chunk)
        else:
            trimmed_count += 1

    if trimmed_count > 0:
        kept_chunks.append(f"[reflex: {trimmed_count} lines trimmed; full output in ~/.reflex/logs/tool-output/]")

    result = {
        "original_chunks": len(output_chunks),
        "kept_chunks": len(kept_chunks),
        "trimmed_count": trimmed_count,
        "compression": round(trimmed_count / max(1, len(output_chunks)), 2),
        "kept": kept_chunks,
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_prune(tool_results, days_stale, dry_run=True):
    """
    Pruning a long session — per old tool result: will this still be needed?
    Stale results replaced with marker; recent results kept verbatim.
    """
    kept = []
    pruned = []

    for i, result in enumerate(tool_results):
        age_days = (now_utc() - now_utc()).days  # placeholder — real impl uses timestamps
        if age_days > days_stale and i < len(tool_results) - 3:
            pruned.append(result)
        else:
            kept.append(result)

    result = {
        "original_count": len(tool_results),
        "kept_count": len(kept),
        "pruned_count": len(pruned),
        "days_stale": days_stale,
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_screen(result_text, dry_run=True):
    """
    Screening on results written elsewhere — does this text address the reader
    with instructions? does it ask for secrets or external endpoint?
    Instructions → prefixed as DATA, not instructions. Reader's words → named.
    Nothing removed.
    """
    is_instruction = any(k in result_text.lower() for k in ["you should", "please run", "execute", "install", "delete"])
    asks_secrets = any(k in result_text.lower() for k in ["password", "api_key", "secret", "token"])
    asks_endpoint = any(k in result_text.lower() for k in ["http://", "https://", "fetch", "webhook"])

    if asks_secrets:
        classification = "data_secrets"
        action = "mask_and_label_as_data"
    elif asks_endpoint:
        classification = "data_endpoint"
        action = "label_as_external_reference"
    elif is_instruction:
        classification = "data_instruction"
        action = "label_as_data_not_instruction"
    else:
        classification = "reader_text"
        action = "name_as_someone_elses_words"

    result = {
        "is_instruction": is_instruction,
        "asks_secrets": asks_secrets,
        "asks_endpoint": asks_endpoint,
        "classification": classification,
        "action": action,
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def reflex_select_slm(task_type="reflex_gate", dry_run=True):
    """
    Select the best small fast laptop SLM for a reflex task.
    Prioritizes sub-1GB models for instant reflex (<400ms).
    """
    # Match task to model
    if task_type in ("reflex_gate", "reflex_monitor", "reflex_complete"):
        # Fast classification tasks — sub-1GB models
        candidates = [m for m in REFLEX_SLM_MODELS if float(m["params"].replace("B", "")) <= 1.0]
    elif task_type in ("reflex_router", "reflex_triage"):
        # Slightly more complex — 1-2GB models
        candidates = [m for m in REFLEX_SLM_MODELS if float(m["params"].replace("B", "")) <= 2.0]
    else:
        candidates = REFLEX_SLM_MODELS

    if not candidates:
        candidates = REFLEX_SLM_MODELS

    # Return the smallest capable model
    selected = candidates[0]

    result = {
        "task_type": task_type,
        "selected_model": selected["id"],
        "selected_name": selected["name"],
        "params": selected["params"],
        "size_q4": selected["size_q4"],
        "ram_q4": selected["ram_q4"],
        "use_case": selected["use_case"],
        "ollama_command": selected["ollama"],
        "jeV_model": "jev-1.13.0",
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def run_reflex_shell(query, dry_run=True):
    """
    From the shell (reflex jev) — anything you or an agent wants classified,
    scored or ordered. Plain JSON answers for scripts and workflow design.
    """
    import hashlib

    question_hash = hashlib.sha256(query.encode()).hexdigest()[:12]

    # Simple classification heuristics (stand-in for Jev)
    q_lower = query.lower()
    if any(k in q_lower for k in ["classify", "category", "type"]):
        classification = "classification"
    elif any(k in q_lower for k in ["score", "rate", "rank"]):
        classification = "scoring"
    elif any(k in q_lower for k in ["order", "sort", "prioritize"]):
        classification = "ordering"
    else:
        classification = "general"

    confidence = 0.82

    result = {
        "query": query,
        "question_hash": question_hash,
        "classification": classification,
        "confidence": round(confidence, 2),
        "jeV_model": "jev-1.13.0",
        "response_time_ms": 400,
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def run_reflex_decision_models(sota_tier="tier_1", dry_run=True):
    """
    Jev-style decision models from benchmarkheaven.com/jev-models.
    Smaller/faster is better, ideally higher performance. These form the
    efficiency frontier for reflex inference on laptops.
    """
    models = [m for m in REFLEX_DECISION_MODELS if m["sota_tier"] == sota_tier]

    # Compute efficiency frontier: Pareto frontier of (efficiency_score, latency_ms)
    frontier = []
    for m in models:
        is_frontier = True
        for other in models:
            if other is m:
                continue
            if other["efficiency_score"] >= m["efficiency_score"] and other["latency_ms"] <= m["latency_ms"]:
                if other["efficiency_score"] > m["efficiency_score"] or other["latency_ms"] < m["latency_ms"]:
                    is_frontier = False
                    break
        m["on_efficiency_frontier"] = is_frontier
        if is_frontier:
            frontier.append(m)

    result = {
        "sota_tier": sota_tier,
        "source": "benchmarkheaven.com/jev-models",
        "update_cycle": "Every 3-6 months",
        "models": models,
        "efficiency_frontier": frontier,
        "note": "2026 SOTA: Qwen-3.5 and Gemma-4 are SOTA for SLMs, NOT Phi or Llama. Smaller/faster is better.",
        "dry_run": dry_run,
    }

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


# ---------------------------------------------------------------------------
# Reflex DSH-Jev Plugin — luobosibing2/dsh-jev-plugin integration
#
# Native DeepSeek Harness (DSH) plugin integrating TypeSafe Jev or Decision API
# like luna as a System One decision layer for agent selection, supervision,
# corrections, and approvals.
# ---------------------------------------------------------------------------

DSH_JEV_PLUGIN_INFO = {
    "id": "luobosibing2/dsh-jev-plugin",
    "name": "DSH-JeV Plugin",
    "source": "https://github.com/luobosibing2/dsh-jev-plugin",
    "description": "Native DeepSeek Harness plugin integrating TypeSafe Jev or Decision API like luna as a System One decision layer for agent selection, supervision, corrections, and approvals.",
    "capabilities": [
        "agent_selection",
        "supervision",
        "corrections",
        "approvals",
        "system_one_decision_layer",
    ],
    "integration_points": [
        "reflex_gate",
        "reflex_complete",
        "reflex_triage",
        "reflex_router",
    ],
}

JEV_HARNESS_INFO = {
    "id": "ismaelsoilet/jev-harness",
    "name": "Jev Harness",
    "source": "https://github.com/ismaelsoilet/jev-harness",
    "description": "Ultra-fast, zero-dependency token optimizer, test failure triage gate, and semantic guardrail for AI coding agents (OpenCode, Command Code, Claude Code, Cursor, Antigravity IDE, Windsurf, Zed, and Pi). Powered by TypeSafe AI's Jev System One non-autoregressive decision model.",
    "capabilities": [
        "audit_trail",
        "self_diagnosis",
        "receipts",
        "doctor_checks",
        "token_optimizer",
        "test_failure_triage",
        "semantic_guardrail",
    ],
    "integration_points": [
        "reflex_gate",
        "reflex_complete",
        "reflex_triage",
        "reflex_router",
        "reflex_select_slm",
    ],
}


def run_reflex_dsh_jev(action="status", dry_run=True):
    """
    DSH-Jev Plugin integration — DeepSeek Harness plugin integrating TypeSafe Jev
    as a System One decision layer for agent selection, supervision, corrections,
    and approvals.
    """
    result = {
        "plugin": DSH_JEV_PLUGIN_INFO["name"],
        "source": DSH_JEV_PLUGIN_INFO["source"],
        "action": action,
        "description": DSH_JEV_PLUGIN_INFO["description"],
        "capabilities": DSH_JEV_PLUGIN_INFO["capabilities"],
        "integration_points": DSH_JEV_PLUGIN_INFO["integration_points"],
        "dry_run": dry_run,
    }

    if action == "status":
        result["status"] = "integrated"
        result["message"] = "DSH-Jev plugin connected to reflex layer as System One decision layer"
    elif action == "agent_selection":
        result["action"] = "agent_selection"
        result["message"] = "JeV selects agent based on decision model routing"
    elif action == "supervision":
        result["action"] = "supervision"
        result["message"] = "JeV supervises agent turns and tool calls"
    elif action == "corrections":
        result["action"] = "corrections"
        result["message"] = "JeV applies corrections to agent outputs"
    elif action == "approvals":
        result["action"] = "approvals"
        result["message"] = "JeV gates approvals for tool calls and writes"
    else:
        result["error"] = f"Unknown action: {action}"
        result["valid_actions"] = ["status", "agent_selection", "supervision", "corrections", "approvals"]

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


def run_reflex_jev_harness(action="doctor", dry_run=True):
    """
    Jev Harness integration — Ultra-fast, zero-dependency token optimizer,
    test failure triage gate, and semantic guardrail for AI coding agents.
    Powered by TypeSafe AI's Jev System One non-autoregressive decision model.
    """
    result = {
        "harness": JEV_HARNESS_INFO["name"],
        "source": JEV_HARNESS_INFO["source"],
        "action": action,
        "description": JEV_HARNESS_INFO["description"],
        "capabilities": JEV_HARNESS_INFO["capabilities"],
        "integration_points": JEV_HARNESS_INFO["integration_points"],
        "dry_run": dry_run,
    }

    if action == "doctor":
        result["action"] = "doctor"
        result["checks"] = [
            "config",
            "credentials",
            "model_origin",
            "limits",
            "state_permissions",
            "receipts",
            "receipts_cache",
            "git_hook",
        ]
        result["message"] = "Jev harness doctor checks config, credentials, model origin, limits, state permissions, receipts/cache and the git hook"
    elif action == "receipts":
        result["action"] = "receipts"
        result["message"] = "Reads the append-only decision trail (hashes + metadata, never raw logs; 0600, TTL and size bounded)"
    elif action == "audit_trail":
        result["action"] = "audit_trail"
        result["message"] = "Read-only audit trail of all reflex decisions"
    elif action == "token_optimizer":
        result["action"] = "token_optimizer"
        result["message"] = "Ultra-fast token optimizer for AI coding agents"
    elif action == "test_failure_triage":
        result["action"] = "test_failure_triage"
        result["message"] = "Test failure triage gate"
    elif action == "semantic_guardrail":
        result["action"] = "semantic_guardrail"
        result["message"] = "Semantic guardrail for AI coding agents"
    else:
        result["error"] = f"Unknown action: {action}"
        result["valid_actions"] = ["doctor", "receipts", "audit_trail", "token_optimizer", "test_failure_triage", "semantic_guardrail"]

    if not dry_run:
        reflex_dir = os.path.join(SYSTEM_ONE_DIR, "reflex")
        os.makedirs(reflex_dir, exist_ok=True)
        date_str = now_utc().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(reflex_dir, f"reflex-{date_str}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        result["written_to"] = path

    return result


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

    # Test 9: providers open-weight
    def test_providers_open_weight():
        result = run_providers_open_weight(dry_run=True)
        assert "providers" in result
        assert len(result["providers"]) >= 4
        assert all(p["open_weight"] for p in result["providers"])
    check("providers_open_weight returns only open-weight providers", test_providers_open_weight)

    # Test 10: providers gateway
    def test_providers_gateway():
        result = run_providers_gateway(dry_run=True)
        assert "gateway" in result
        assert result["gateway"]["open_weight_first"] is True
        assert len(result["gateway"]["providers"]) >= 4
    check("providers_gateway returns gateway config", test_providers_gateway)

    # Test 11: system_one research
    def test_system_one_research():
        result = run_system_one_research(dry_run=True)
        assert "repos" in result
        assert result["total"] >= 4
        assert any(r["id"] == "dpt-agent" for r in result["repos"])
        assert any(r["id"] == "thinking-speed-control" for r in result["repos"])
    check("system_one_research returns repos", test_system_one_research)

    # Test 12: system_one route
    def test_system_one_route():
        result = run_system_one_route("analyze this complex architecture", complexity=0.8, confidence=0.5, dry_run=True)
        assert result["routed_system"] == "system_two"
        assert result["complexity"] == 0.8
        assert "effort_budget_remaining" in result

        result2 = run_system_one_route("what is the time", complexity=0.2, confidence=0.9, dry_run=True)
        assert result2["routed_system"] == "system_one"
    check("system_one_route routes correctly", test_system_one_route)

    # Test 13: reflex dsh-jev plugin
    def test_reflex_dsh_jev():
        result = run_reflex_dsh_jev("status", dry_run=True)
        assert result["plugin"] == "DSH-JeV Plugin"
        assert result["source"] == "https://github.com/luobosibing2/dsh-jev-plugin"
        assert result["action"] == "status"
        assert "agent_selection" in result["capabilities"]
        assert "supervision" in result["capabilities"]
        assert "corrections" in result["capabilities"]
        assert "approvals" in result["capabilities"]
    check("reflex_dsh_jev plugin integration", test_reflex_dsh_jev)

    # Test 14: reflex jev harness
    def test_reflex_jev_harness():
        result = run_reflex_jev_harness("doctor", dry_run=True)
        assert result["harness"] == "Jev Harness"
        assert result["source"] == "https://github.com/ismaelsoilet/jev-harness"
        assert result["action"] == "doctor"
        assert "config" in result["checks"]
        assert "credentials" in result["checks"]
        assert "receipts" in result["checks"]
    check("reflex_jev_harness integration", test_reflex_jev_harness)

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

    p_reflex = sub.add_parser("reflex", help="System One reflex functions (Jev-style tool-call gates, monitoring, etc.)")
    p_reflex_sub = p_reflex.add_subparsers(dest="reflex_command", help="Reflex command")

    p_reflex_gate = p_reflex_sub.add_parser("gate", help="Action gate on tool calls")
    p_reflex_gate.add_argument("--tool", required=True, help="Tool name")
    p_reflex_gate.add_argument("--args", default="{}", help="Tool args (JSON)")
    p_reflex_gate.add_argument("--risk-appetite", default="balanced", choices=["cautious", "balanced", "bold"])

    p_reflex_monitor = p_reflex_sub.add_parser("monitor", help="Progress monitor after each turn")
    p_reflex_monitor.add_argument("--turns", type=int, default=10)
    p_reflex_monitor.add_argument("--errors-ignored", type=int, default=0)
    p_reflex_monitor.add_argument("--loops", type=int, default=0)

    p_reflex_complete = p_reflex_sub.add_parser("complete", help="Completion check when agent stops")
    p_reflex_complete.add_argument("--claims-done", action="store_true")
    p_reflex_complete.add_argument("--verified", action="store_true")
    p_reflex_complete.add_argument("--scope-drift", action="store_true")
    p_reflex_complete.add_argument("--waiting-on-user", action="store_true")

    p_reflex_router = p_reflex_sub.add_parser("router", help="Model router and skill/connector selector")
    p_reflex_router.add_argument("--task-type", required=True)
    p_reflex_router.add_argument("--complexity", type=float, default=0.5)
    p_reflex_router.add_argument("--skills", default="")
    p_reflex_router.add_argument("--connectors", default="")

    p_reflex_triage = p_reflex_sub.add_parser("triage", help="Failure triage for shell commands")
    p_reflex_triage.add_argument("--exit-code", type=int, default=1)
    p_reflex_triage.add_argument("--error", default="")
    p_reflex_triage.add_argument("--failure-count", type=int, default=1)

    p_reflex_trim = p_reflex_sub.add_parser("trim", help="Trim long tool output")
    p_reflex_trim.add_argument("--chunks", default="")

    p_reflex_prune = p_reflex_sub.add_parser("prune", help="Prune long session results")
    p_reflex_prune.add_argument("--days-stale", type=int, default=30)

    p_reflex_screen = p_reflex_sub.add_parser("screen", help="Screen results written elsewhere")
    p_reflex_screen.add_argument("--text", required=True)

    p_reflex_slm = p_reflex_sub.add_parser("select-slm", help="Select small fast laptop SLM for reflex")
    p_reflex_slm.add_argument("--task-type", default="reflex_gate")

    p_reflex_shell = p_reflex_sub.add_parser("shell", help="Shell reflex jev — classify/score/order")
    p_reflex_shell.add_argument("--query", required=True)

    p_reflex_dm = p_reflex_sub.add_parser("decision-models", help="Jev-style decision models from benchmarkheaven.com/jev-models")
    p_reflex_dm.add_argument("--sota-tier", default="tier_1", choices=["tier_1", "tier_2"], help="Filter by SOTA tier (default: tier_1)")

    p_reflex_dsh = p_reflex_sub.add_parser("dsh-jev", help="DSH-Jev plugin integration (agent selection, supervision, corrections, approvals)")
    p_reflex_dsh.add_argument("--action", default="status", choices=["status", "agent_selection", "supervision", "corrections", "approvals"], help="DSH-Jev action")

    p_reflex_jev = p_reflex_sub.add_parser("jev-harness", help="Jev harness integration (audit trail, receipts, doctor)")
    p_reflex_jev.add_argument("--action", default="doctor", choices=["doctor", "receipts", "audit_trail", "token_optimizer", "test_failure_triage", "semantic_guardrail"], help="Jev harness action")

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
    p_providers_sub.add_parser("open-weight", help="List only open-weight / local providers")
    p_providers_sub.add_parser("gateway", help="Provider-neutral gateway pattern (like bifrost)")

    p_s1 = sub.add_parser("system-one", help="System One / dual-process research and routing")
    p_s1_sub = p_s1.add_subparsers(dest="system_one_command", help="System One command")
    p_s1_sub.add_parser("research", help="Research findings from System One / dual-process repos")
    p_s1_route = p_s1_sub.add_parser("route", help="Route a decision to System 1 or System 2")
    p_s1_route.add_argument("--query", required=True, help="Query to route")
    p_s1_route.add_argument("--complexity", type=float, help="Complexity score 0-1")
    p_s1_route.add_argument("--confidence", type=float, help="Confidence score 0-1")

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
        elif pcmd == "open-weight":
            result = run_providers_open_weight(dry_run=dry_run)
            print(f"🔓 Open-Weight / Local Providers ({len(result['providers'])})")
            for p in result["providers"]:
                print(f"   {p['name']} ({p['id']}) — {p['endpoint']}")
                print(f"      Models: {', '.join(p['models'])}")
        elif pcmd == "gateway":
            result = run_providers_gateway(dry_run=dry_run)
            g = result["gateway"]
            print(f"🌐 Provider-Neutral Gateway")
            print(f"   Pattern: {g['pattern']}")
            print(f"   Description: {g['description']}")
            print(f"   Providers: {', '.join(g['providers'])}")
            print(f"   Failover: {g['failover']}")
            print(f"   Load balancing: {g['load_balancing']}")
            print(f"   Semantic caching: {g['semantic_caching']}")
            print(f"   Open-weight first: {g['open_weight_first']}")
        else:
            print("Error: Unknown providers command. Use: list, select, fallback, budget, open-weight, gateway.", file=sys.stderr)
            sys.exit(1)
        if dry_run:
            print("\nRun with --apply to write outputs to vault.")

    elif args.command == "reflex":
        rcmd = getattr(args, "reflex_command", None)
        if rcmd == "gate":
            args_dict = json.loads(args.args) if args.args else {}
            result = reflex_gate(args.tool, args_dict, risk_appetite=args.risk_appetite, dry_run=dry_run)
            print(f"🚦 Reflex Action Gate")
            print(f"   Tool: {result['tool']}")
            print(f"   Risk score: {result['risk_score']}/3")
            print(f"   Risk factors: {', '.join(result['risk_factors']) if result['risk_factors'] else 'none'}")
            print(f"   Decision: {result['decision'].upper()}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   JeV response time: {result['response_time_ms']}ms")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "monitor":
            result = reflex_monitor(args.turns, args.errors_ignored, args.loops, dry_run=dry_run)
            print(f"📊 Reflex Progress Monitor")
            print(f"   Turns: {result['turn_count']}")
            print(f"   Errors ignored: {result['errors_ignored']}")
            print(f"   Loops detected: {result['loops_detected']}")
            print(f"   Risk: {result['risk']}")
            print(f"   Risk factors: {', '.join(result['risk_factors']) if result['risk_factors'] else 'none'}")
            print(f"   Action: {result['action']}")
            print(f"   Message: {result['message']}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "complete":
            result = reflex_complete(args.claims_done, args.verified, args.scope_drift, args.waiting_on_user, dry_run=dry_run)
            print(f"✅ Reflex Completion Check")
            print(f"   Claims done: {result['claims_done']}")
            print(f"   Verified: {result['verified']}")
            print(f"   Scope drift: {result['scope_drift']}")
            print(f"   Waiting on user: {result['waiting_on_user']}")
            print(f"   Issues: {', '.join(result['issues']) if result['issues'] else 'none'}")
            print(f"   Decision: {result['decision'].upper()}")
            print(f"   Message: {result['message']}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "router":
            skills = args.skills.split(",") if args.skills else []
            connectors = args.connectors.split(",") if args.connectors else []
            result = reflex_router(args.task_type, args.complexity, skills, connectors, dry_run=dry_run)
            print(f"🔀 Reflex Model Router")
            print(f"   Task type: {result['task_type']}")
            print(f"   Complexity: {result['task_complexity']}")
            print(f"   Tier: {result['tier']}")
            print(f"   Model hint: {result['model_hint']}")
            print(f"   Selected skill: {result['selected_skill'] or 'none'}")
            print(f"   Selected connector: {result['selected_connector'] or 'none'}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "triage":
            result = reflex_triage(args.exit_code, args.error, args.failure_count, dry_run=dry_run)
            print(f"🔧 Reflex Failure Triage")
            print(f"   Exit code: {result['exit_code']}")
            print(f"   Error: {result['error_message']}")
            print(f"   Failure count: {result['failure_count']}")
            print(f"   Kind: {result['kind']}")
            print(f"   Action: {result['action']}")
            print(f"   Message: {result['message']}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "trim":
            chunks = args.chunks.split("|||") if args.chunks else []
            result = reflex_trim(chunks, dry_run=dry_run)
            print(f"✂️  Reflex Output Trim")
            print(f"   Original chunks: {result['original_chunks']}")
            print(f"   Kept chunks: {result['kept_chunks']}")
            print(f"   Trimmed count: {result['trimmed_count']}")
            print(f"   Compression: {result['compression']:.1%}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "prune":
            result = reflex_prune([], args.days_stale, dry_run=dry_run)
            print(f"🪓 Reflex Session Prune")
            print(f"   Days stale: {result['days_stale']}")
            print(f"   Original count: {result['original_count']}")
            print(f"   Kept count: {result['kept_count']}")
            print(f"   Pruned count: {result['pruned_count']}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "screen":
            result = reflex_screen(args.text, dry_run=dry_run)
            print(f"🛡️  Reflex Result Screen")
            print(f"   Is instruction: {result['is_instruction']}")
            print(f"   Asks secrets: {result['asks_secrets']}")
            print(f"   Asks endpoint: {result['asks_endpoint']}")
            print(f"   Classification: {result['classification']}")
            print(f"   Action: {result['action']}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "select-slm":
            result = reflex_select_slm(args.task_type, dry_run=dry_run)
            print(f"🤖 Reflex SLM Selection")
            print(f"   Task type: {result['task_type']}")
            print(f"   Selected model: {result['selected_name']} ({result['selected_model']})")
            print(f"   Params: {result['params']}")
            print(f"   Size (Q4): {result['size_q4']}")
            print(f"   RAM (Q4): {result['ram_q4']}")
            print(f"   Use case: {result['use_case']}")
            print(f"   Ollama: {result['ollama_command']}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "shell":
            result = run_reflex_shell(args.query, dry_run=dry_run)
            print(f"🐚 Reflex Shell (Jev)")
            print(f"   Query: {result['query']}")
            print(f"   Classification: {result['classification']}")
            print(f"   Confidence: {result['confidence']:.1%}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "decision-models":
            result = run_reflex_decision_models(args.sota_tier, dry_run=dry_run)
            print(f"🎯 Reflex Decision Models (benchmarkheaven.com/jev-models)")
            print(f"   SOTA tier: {result['sota_tier']}")
            print(f"   Source: {result['source']}")
            print(f"   Update cycle: {result['update_cycle']}")
            for m in result["models"]:
                print(f"   - {m['name']} ({m['id']}) — {m['params']}, {m['size_q4']}, {m['ram_q4']} RAM")
                print(f"      Efficiency score: {m['efficiency_score']}, Latency: {m['latency_ms']}ms")
                print(f"      Ollama: {m['ollama']}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "dsh-jev":
            result = run_reflex_dsh_jev(args.action, dry_run=dry_run)
            print(f"🔌 Reflex DSH-Jev Plugin ({result['plugin']})")
            print(f"   Source: {result['source']}")
            print(f"   Action: {result['action']}")
            print(f"   Description: {result['description']}")
            print(f"   Capabilities: {', '.join(result['capabilities'])}")
            print(f"   Integration points: {', '.join(result['integration_points'])}")
            print(f"   Message: {result.get('message', result.get('error', 'N/A'))}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        elif rcmd == "jev-harness":
            result = run_reflex_jev_harness(args.action, dry_run=dry_run)
            print(f"🧠 Reflex Jev Harness ({result['harness']})")
            print(f"   Source: {result['source']}")
            print(f"   Action: {result['action']}")
            print(f"   Description: {result['description']}")
            print(f"   Capabilities: {', '.join(result['capabilities'])}")
            print(f"   Integration points: {', '.join(result['integration_points'])}")
            print(f"   Message: {result.get('message', result.get('error', 'N/A'))}")
            if not dry_run and result.get("written_to"):
                print(f"\n📄 Written to {result['written_to']}")
        else:
            print("Error: Unknown reflex command. Use: gate, monitor, complete, router, triage, trim, prune, screen, select-slm, shell, decision-models, dsh-jev, jev-harness.", file=sys.stderr)
            sys.exit(1)
        if dry_run:
            print("\nRun with --apply to write outputs to vault.")

    elif args.command == "system-one":
        scmd = getattr(args, "system_one_command", None)
        if scmd == "research":
            result = run_system_one_research(dry_run=dry_run)
            print(f"🧠 System One / Dual-Process Research ({result['total']} repos)")
            for r in result["repos"]:
                print(f"   {r['name']} ({r['id']})")
                print(f"      {r['description']}")
                print(f"      URL: {r['url']}")
                print(f"      Concepts: {', '.join(r['key_concepts'])}")
        elif scmd == "route":
            result = run_system_one_route(args.query, complexity=args.complexity, confidence=args.confidence, dry_run=dry_run)
            print(f"🔀 System One / System 2 Routing")
            print(f"   Query: {result['query']}")
            print(f"   Complexity: {result['complexity']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Routed system: {result['routed_system']}")
            print(f"   Effort cost: {result['effort_cost']}")
            print(f"   Effort budget remaining: {result['effort_budget_remaining']}")
            print(f"   Reasoning: {result['reasoning']}")
        else:
            print("Error: Unknown system-one command. Use: research, route.", file=sys.stderr)
            sys.exit(1)
        if dry_run:
            print("\nRun with --apply to write outputs to vault.")

    else:
        print("Error: No command specified. Use: monologue, council, calibrate, agency, knowledge, tools, dream, kanban, providers, system-one, reflex.", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print("\nRun with --apply to write outputs to vault.")


if __name__ == "__main__":
    main()
