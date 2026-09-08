#!/usr/bin/env python3
"""
consolidate_memory.py — nightly "dream cycle" for the Hermes Brain Obsidian vault.

Inspired by open-second-brain / brainstack (typed memory + nightly consolidation),
but implemented from scratch, stdlib-only, tailored to this vault's existing
Daily -> Memory-Review -> native-memory pipeline described in
Projects/Hermes-Agent-Vault-Setup.md and Memory-Review/TEMPLATE.md.

What it does (mechanical only — NEVER touches Hermes's real MEMORY.md/USER.md):
  1. Parses raw fact sources:
       - Memory-Review/Supermemory-All-Memory-Entries.md  (bullet list, grouped by ## date)
       - Memory-Review/Supermemory-Explicit-Memories.md   (markdown table)
  2. Re-reads the previous Memory-Review/Promotion-Candidates.md (if any) to see
     which candidates Sid already checked off (decided) — those are archived to
     Memory-Review/Consolidation-Log.md and never shown again.
  3. Strips out anything that looks like a secret/credential (regex) into
     Memory-Review/Excluded-Sensitive.md — these are NEVER proposed for promotion.
  4. Dedupes near-identical facts (difflib ratio) against each other and against
     already-decided facts.
  5. Flags candidates that have sat undecided for 60+ days as "stale — reconsider"
     (a decay signal, not an auto-delete — Sid still decides).
  6. Rewrites Memory-Review/Promotion-Candidates.md: one checkbox per still-open
     candidate, grouped by source date, ready for a human approval pass before
     anything is manually copied into native MEMORY.md/USER.md.

Usage:
    python consolidate_memory.py <vault_root>

Exit code 0 always (this is a reporting/staging tool, not a gate); prints a short
summary to stdout for cron delivery.
"""
import sys
import os
import re
import json
import hashlib
import difflib
from datetime import datetime, timezone

STALE_DAYS = 60

SECRET_PATTERNS = [
    re.compile(r"api[_-]?key", re.I),
    re.compile(r"secret[_-]?key", re.I),
    re.compile(r"\bpassword\b", re.I),
    re.compile(r"\bbearer\s+[a-z0-9._-]{10,}", re.I),
    re.compile(r"\btoken\b.{0,20}[:=]\s*['\"]?[a-z0-9._-]{16,}", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bssh-(rsa|ed25519)\s+[A-Za-z0-9+/=]{20,}"),
    re.compile(r"\b[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}\b"),  # jwt-ish
]

TRANSIENT_HINTS = [
    "is stopped", "no longer responding", "shut down", "shutdown confirmation",
    "was created", "test confirmation", "echo test", "verified functional after",
    "successfully tested",
]


def read(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def fact_hash(text):
    norm = re.sub(r"_\(session `[^`]+`\)_", "", text)
    norm = re.sub(r"\s+", " ", norm).strip().lower()
    norm = re.sub(r"[^a-z0-9 ]", "", norm)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest(), norm


def is_secret(text):
    return any(p.search(text) for p in SECRET_PATTERNS)


def is_likely_transient(text):
    low = text.lower()
    return any(h in low for h in TRANSIENT_HINTS)


def parse_bullet_entries(md_text):
    """Parse Supermemory-All-Memory-Entries.md: '## YYYY-MM-DD' headers, '- fact' bullets."""
    entries = []
    current_date = None
    for line in md_text.splitlines():
        m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$", line.strip())
        if m:
            current_date = m.group(1)
            continue
        m = re.match(r"^-\s+(.*)$", line.strip())
        if m and current_date:
            entries.append({"date": current_date, "text": m.group(1).strip()})
    return entries


def parse_table_entries(md_text):
    """Parse Supermemory-Explicit-Memories.md: markdown table | Title | Created | Summary |."""
    entries = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Title"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 3:
            title, created, summary = cols[0], cols[1], "|".join(cols[2:])
            if re.match(r"\d{4}-\d{2}-\d{2}", created):
                entries.append({"date": created, "text": f"{title} — {summary}"})
    return entries


def parse_decided_from_candidates(md_text):
    """Read back a previous Promotion-Candidates.md; return {hash: decision} for checked boxes."""
    decided = {}
    for line in md_text.splitlines():
        m = re.match(r"^- \[(x|X)\]\s+(.*?)\s+`#([a-f0-9]{8})`\s*$", line.strip())
        if m:
            decided[m.group(3)] = line.strip()
    return decided


def main():
    if len(sys.argv) < 2:
        print("usage: consolidate_memory.py <vault_root>")
        sys.exit(1)
    vault = sys.argv[1]
    mr_dir = os.path.join(vault, "Memory-Review")
    os.makedirs(mr_dir, exist_ok=True)

    all_entries_path = os.path.join(mr_dir, "Supermemory-All-Memory-Entries.md")
    explicit_path = os.path.join(mr_dir, "Supermemory-Explicit-Memories.md")
    candidates_path = os.path.join(mr_dir, "Promotion-Candidates.md")
    excluded_path = os.path.join(mr_dir, "Excluded-Sensitive.md")
    log_path = os.path.join(mr_dir, "Consolidation-Log.md")
    state_path = os.path.join(mr_dir, ".consolidate_state.json")

    raw = parse_bullet_entries(read(all_entries_path)) + parse_table_entries(read(explicit_path))

    # Load prior state: hashes already decided (approved/archived) in past runs.
    state = {"decided_hashes": {}, "first_seen": {}}
    if os.path.exists(state_path):
        try:
            state = json.loads(read(state_path))
        except Exception:
            pass
    state.setdefault("decided_hashes", {})
    state.setdefault("first_seen", {})

    # Read back the previous candidates file for newly-checked boxes since last run.
    prev_candidates_text = read(candidates_path)
    newly_decided = parse_decided_from_candidates(prev_candidates_text)
    newly_archived = []
    for h, line in newly_decided.items():
        if h not in state["decided_hashes"]:
            state["decided_hashes"][h] = {
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "line": line,
            }
            newly_archived.append(line)

    # Append newly-decided items to the durable Consolidation-Log.md (audit trail).
    if newly_archived:
        with open(log_path, "a", encoding="utf-8") as f:
            if os.path.getsize(log_path) == 0 if os.path.exists(log_path) else True:
                f.write("# Consolidation Log\n\nAudit trail of candidates Sid has already decided on. "
                        "Appended automatically by Scripts/consolidate_memory.py — never edited by hand.\n\n")
            f.write(f"## Run {datetime.now(timezone.utc).isoformat()}\n")
            for line in newly_archived:
                f.write(f"{line}\n")
            f.write("\n")

    # Bucket incoming facts: secret / transient-flag / normal, dedupe by hash.
    # decided_hashes is keyed by the 8-char tag shown in Promotion-Candidates.md
    # (that tag is the candidate's public identity), so compare on h[:8] here too -
    # comparing the full 40-char hash against those 8-char keys never matched,
    # which meant already-decided candidates kept reappearing on every run.
    decided_prefixes = set(state["decided_hashes"].keys())
    seen_hashes = set()  # full-hash dedupe within this run
    excluded_secrets = []
    grouped = {}  # date -> list of (hash, text, flags)
    dup_count = 0
    new_count = 0

    for e in raw:
        text = e["text"]
        h, norm = fact_hash(text)
        if is_secret(text):
            excluded_secrets.append((e["date"], text))
            continue
        if h[:8] in decided_prefixes or h in seen_hashes:
            dup_count += 1
            continue
        seen_hashes.add(h)  # dedupe within this run too
        flags = []
        if is_likely_transient(text):
            flags.append("transient")
        first_seen = state["first_seen"].get(h)
        if not first_seen:
            state["first_seen"][h] = datetime.now(timezone.utc).isoformat()
            new_count += 1
        else:
            age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(first_seen)).days
            if age_days >= STALE_DAYS:
                flags.append(f"stale {age_days}d")
        grouped.setdefault(e["date"], []).append((h, text, flags))

    # Fuzzy dedupe within each date group (catches near-identical rephrasings).
    for date, items in grouped.items():
        kept = []
        for h, text, flags in items:
            is_dup = False
            for kh, ktext, kflags in kept:
                if difflib.SequenceMatcher(None, text.lower(), ktext.lower()).ratio() > 0.90:
                    is_dup = True
                    dup_count += 1
                    break
            if not is_dup:
                kept.append((h, text, flags))
        grouped[date] = kept

    # Write excluded-sensitive log (append-only, never promoted, never shown as candidate).
    if excluded_secrets:
        with open(excluded_path, "a", encoding="utf-8") as f:
            if not os.path.exists(excluded_path) or os.path.getsize(excluded_path) == 0:
                f.write("# Excluded — Sensitive Content\n\n"
                        "Facts auto-detected as containing credentials/secrets. Automatically "
                        "excluded from Promotion-Candidates.md — never promoted to native memory. "
                        "Review manually if something looks miscategorized.\n\n")
            f.write(f"## Run {datetime.now(timezone.utc).isoformat()}\n")
            for date, text in excluded_secrets:
                f.write(f"- [{date}] {text[:200]}\n")
            f.write("\n")

    # Rewrite Promotion-Candidates.md with all still-open candidates.
    lines = []
    lines.append("# Promotion Candidates (auto-consolidated)")
    lines.append("")
    lines.append(f"Regenerated {datetime.now(timezone.utc).isoformat()} by `Scripts/consolidate_memory.py`. "
                  "Check a box and re-run the script to archive your decision to "
                  "[[Consolidation-Log]] — nothing here is auto-promoted to native "
                  "MEMORY.md/USER.md, that step stays manual per [[TEMPLATE|Memory-Review criteria]].")
    lines.append("")
    lines.append(f"- New this run: **{new_count}** · Deduped/skipped: **{dup_count}** · "
                  f"Sensitive excluded: **{len(excluded_secrets)}** (see [[Excluded-Sensitive]])")
    lines.append("")
    lines.append("Mark `[x]` for PROMOTE, or just leave `[ ]` to keep pending / delete the line "
                  "to reject outright. `stale Nd` = undecided 60+ days, reconsider archiving instead.")
    lines.append("")

    for date in sorted(grouped.keys(), reverse=True):
        items = grouped[date]
        if not items:
            continue
        lines.append(f"## {date}")
        for h, text, flags in items:
            flag_str = f" _({', '.join(flags)})_" if flags else ""
            lines.append(f"- [ ] {text}{flag_str} `#{h[:8]}`")
        lines.append("")

    with open(candidates_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    total_open = sum(len(v) for v in grouped.values())
    print(f"[consolidate_memory] archived {len(newly_archived)} decided candidate(s) to Consolidation-Log.md; "
          f"{new_count} new, {dup_count} deduped, {len(excluded_secrets)} sensitive excluded, "
          f"{total_open} candidates now pending review in Promotion-Candidates.md")


if __name__ == "__main__":
    main()
