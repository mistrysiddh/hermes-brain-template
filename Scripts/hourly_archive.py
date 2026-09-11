#!/usr/bin/env python3
"""
Hermes Brain — hourly session archiver + token tracker.

Exports Hermes chat sessions active in the last hour as redacted markdown,
reorganizes them into the vault's Daily/YYYY/MM/DD/ convention, maintains
a deduplicated manifest.jsonl, AND extracts token usage from JSONL export
to maintain a running total in Skills-Notes/Token-Usage.log.

Only ONE cron job should ever run this against a given vault, to avoid
manifest.jsonl races (see Daily/README.md).
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

VAULT = os.environ.get("HERMES_VAULT_PATH")
if not VAULT:
    print("HERMES_VAULT_PATH is not set — aborting.")
    sys.exit(1)

DAILY = os.path.join(VAULT, "Daily")
os.makedirs(DAILY, exist_ok=True)
MANIFEST = os.path.join(DAILY, "manifest.jsonl")
TOKEN_LOG = os.path.join(VAULT, "Skills-Notes", "Token-Usage.log")

CREATED_RE = re.compile(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})')

def find_hermes():
    for cand in ("hermes", shutil.which("hermes")):
        if cand and shutil.which(cand):
            return cand
    return "hermes"

def extract_tokens_from_jsonl(jsonl_path):
    """Parse JSONL export and sum prompt+completion tokens per session."""
    total = 0
    sessions = 0
    if not os.path.exists(jsonl_path):
        return total, sessions
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Try to find token usage in model_config
            model_config = rec.get("model_config", "")
            if model_config:
                try:
                    cfg = json.loads(model_config)
                    usage = cfg.get("_usage_anchor", {})
                    prompt = usage.get("prompt_tokens", 0)
                    completion = usage.get("completion_tokens", 0)
                    total += prompt + completion
                    sessions += 1
                except (json.JSONDecodeError, TypeError):
                    pass
    return total, sessions

def update_token_log(daily_total, session_count):
    """Append today's token total to the running log."""
    today = datetime.now().strftime("%Y-%m-%d")
    line = f"{today}: {daily_total} tokens ({session_count} session(s))\n"
    os.makedirs(os.path.dirname(TOKEN_LOG), exist_ok=True)
    with open(TOKEN_LOG, "a", encoding="utf-8") as f:
        f.write(line)
    # Also compute and print running total
    running_total = 0
    if os.path.exists(TOKEN_LOG):
        with open(TOKEN_LOG, encoding="utf-8") as f:
            for l in f:
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                parts = l.split(":")
                if len(parts) == 2:
                    try:
                        running_total += int(parts[1].split()[0])
                    except ValueError:
                        pass
    print(f"Token usage today: {daily_total} tokens ({session_count} session(s))")
    print(f"Running total: {running_total:,} tokens")
    return running_total

def main():
    hermes_bin = find_hermes()

    # 1. Export sessions as markdown (for the vault) — existing behavior
    cmd_md = [
        hermes_bin, "sessions", "export",
        "--format", "md",
        "--newer-than", "70m",
        "--redact",
        "--yes",
        DAILY,
    ]
    result_md = subprocess.run(cmd_md, capture_output=True, text=True)
    print(result_md.stdout.strip())
    if result_md.returncode != 0:
        print(result_md.stderr.strip())
        sys.exit(result_md.returncode)

    if "Exported 0 session" in result_md.stdout:
        print("No new sessions this hour.")
        return

    # 2. ALSO export as JSONL to capture token usage (streaming to stdout)
    cmd_jsonl = [
        hermes_bin, "sessions", "export",
        "--format", "jsonl",
        "--newer-than", "70m",
        "--redact",
        "--yes",
        "-",  # stdout
    ]
    result_jsonl = subprocess.run(cmd_jsonl, capture_output=True, text=True)
    if result_jsonl.returncode != 0:
        print(f"Warning: JSONL export failed: {result_jsonl.stderr.strip()}")
        jsonl_path = None
    else:
        # Write JSONL to a temp file for token extraction
        jsonl_path = os.path.join(DAILY, "tmp_export.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            f.write(result_jsonl.stdout)

    # 3. Extract token usage from JSONL
    daily_total = 0
    session_count = 0
    if jsonl_path and os.path.exists(jsonl_path):
        daily_total, session_count = extract_tokens_from_jsonl(jsonl_path)
        update_token_log(daily_total, session_count)
        os.remove(jsonl_path)  # clean up

    # 4. Load existing manifest (dedupe by session_id).
    existing = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
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
                    existing[sid] = rec

    # 5. Move flat exported files into YYYY/MM/DD/, updating manifest paths.
    for fname in os.listdir(DAILY):
        fpath = os.path.join(DAILY, fname)
        if not os.path.isfile(fpath) or not fname.endswith(".md"):
            continue
        # skip vault scaffolding notes
        if fname in ("README.md", "Timeline.md", "Chat-Correlation.md", "tmp_export.jsonl"):
            continue

        with open(fpath, encoding="utf-8") as f:
            head = f.read(2000)

        m = CREATED_RE.search(head)
        if not m:
            continue
        y, mo, d = m.groups()

        sid_m = re.search(r'session_id:\s*"([^"]+)"', head)
        session_id = sid_m.group(1) if sid_m else None

        destdir = os.path.join(DAILY, y, mo, d)
        os.makedirs(destdir, exist_ok=True)
        destpath = os.path.join(destdir, fname)

        if os.path.exists(destpath):
            os.remove(fpath)  # duplicate re-export of same session, drop
        else:
            shutil.move(fpath, destpath)

        if session_id:
            title_m = re.search(r'title:\s*"([^"]*)"', head)
            msgcount_m = re.search(r"message_count:\s*(\d+)", head)
            existing[session_id] = {
                "session_id": session_id,
                "title": title_m.group(1) if title_m else "",
                "path": destpath,
                "format": "md",
                "message_count": int(msgcount_m.group(1)) if msgcount_m else None,
                "exported_at": os.path.getmtime(destpath),
            }

    # 6. Rewrite manifest, sorted by exported_at.
    records = sorted(existing.values(), key=lambda r: r.get("exported_at") or 0)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    print(f"Manifest now has {len(records)} session(s) indexed.")


if __name__ == "__main__":
    main()