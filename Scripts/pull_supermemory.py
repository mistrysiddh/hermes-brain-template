#!/usr/bin/env python3
"""Pull ALL memories for a Supermemory container tag and save to the vault
as both a raw JSON dump and a human-readable markdown note."""
import json
import os
import sys
import time
import urllib.request

API_KEY = os.environ.get("SUPERMEMORY_API_KEY")
CONTAINER_TAG = os.environ.get("SUPERMEMORY_CONTAINER_TAG", "hermes")
VAULT = os.environ.get("HERMES_VAULT_PATH")

if not API_KEY or not VAULT:
    print("Need SUPERMEMORY_API_KEY and HERMES_VAULT_PATH set.")
    sys.exit(1)

URL = "https://api.supermemory.ai/v4/memories/list"
LIMIT = 100

all_entries = []
page = 1
while True:
    body = json.dumps({"containerTags": [CONTAINER_TAG], "limit": LIMIT, "page": page}).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    entries = data.get("memoryEntries", [])
    all_entries.extend(entries)
    pag = data.get("pagination", {})
    total_pages = pag.get("totalPages", 1)
    print(f"page {page}/{total_pages} -> {len(entries)} entries (running total {len(all_entries)})")
    if page >= total_pages or not entries:
        break
    page += 1
    time.sleep(0.2)

out_dir = os.path.join(VAULT, "Research", "Supermemory")
os.makedirs(out_dir, exist_ok=True)

json_path = os.path.join(out_dir, f"{CONTAINER_TAG}-memories.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_entries, f, indent=2, ensure_ascii=False)

# Human-readable markdown, grouped by session_id when available
by_session = {}
loose = []
for e in all_entries:
    sid = (e.get("metadata") or {}).get("session_id")
    if sid:
        by_session.setdefault(sid, []).append(e)
    else:
        loose.append(e)

md_path = os.path.join(out_dir, f"{CONTAINER_TAG}-memories.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# Supermemory export — container `{CONTAINER_TAG}`\n\n")
    f.write(f"Pulled {len(all_entries)} memory entries.\n\n")
    for sid, entries in sorted(by_session.items()):
        entries.sort(key=lambda e: e.get("createdAt", ""))
        f.write(f"## Session `{sid}`\n\n")
        for e in entries:
            f.write(f"- {e.get('memory', '').strip()}\n")
        f.write("\n")
    if loose:
        f.write("## (No session tag)\n\n")
        for e in loose:
            f.write(f"- {e.get('memory', '').strip()}\n")

print(f"Wrote {len(all_entries)} memories to:\n  {json_path}\n  {md_path}")
