#!/usr/bin/env python3
"""
Hermes Brain — hourly session archiver.

Exports Hermes chat sessions active in the last hour as redacted markdown,
then reorganizes them into the vault's Daily/YYYY/MM/DD/ convention
(hermes sessions export only writes flat into the target dir), and merges
their manifest records into a single Daily/manifest.jsonl keyed by
session_id (idempotent — safe to re-run / re-fire for the same hour).

Only ONE cron job should ever run this against a given vault, to avoid
manifest.jsonl races (see Daily/README.md).
"""
import json
import os
import re
import shutil
import subprocess
import sys

VAULT = os.environ.get("HERMES_VAULT_PATH")
if not VAULT:
    print("HERMES_VAULT_PATH is not set — aborting.")
    sys.exit(1)

DAILY = os.path.join(VAULT, "Daily")
os.makedirs(DAILY, exist_ok=True)
MANIFEST = os.path.join(DAILY, "manifest.jsonl")

CREATED_RE = re.compile(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})')


def find_hermes():
    for cand in ("hermes", shutil.which("hermes")):
        if cand and shutil.which(cand):
            return cand
    return "hermes"


def main():
    hermes_bin = find_hermes()

    # 1. Export sessions active in the last hour (with a small overlap
    #    buffer so nothing falls through the cracks between ticks).
    cmd = [
        hermes_bin, "sessions", "export",
        "--format", "md",
        "--newer-than", "70m",
        "--redact",
        "--yes",
        DAILY,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip())
        sys.exit(result.returncode)

    if "Exported 0 session" in result.stdout:
        print("No new sessions this hour.")
        return

    # 2. Load existing manifest (dedupe by session_id).
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

    # 3. Move flat exported files into YYYY/MM/DD/, updating manifest paths.
    for fname in os.listdir(DAILY):
        fpath = os.path.join(DAILY, fname)
        if not os.path.isfile(fpath) or not fname.endswith(".md"):
            continue
        # skip vault scaffolding notes
        if fname in ("README.md", "Timeline.md", "Chat-Correlation.md"):
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

    # 4. Rewrite manifest, sorted by exported_at.
    records = sorted(existing.values(), key=lambda r: r.get("exported_at") or 0)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    print(f"Manifest now has {len(records)} session(s) indexed.")


if __name__ == "__main__":
    main()
