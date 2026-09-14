#!/usr/bin/env python3
"""
Hermes Brain — CI smoke-test fixture builder.

Creates a minimal, throwaway vault under a temp directory so
vault_audit.py and agent_performance.py can be run against real files
and checked for a clean exit + expected output, catching runtime
errors that syntax-only linting can't (see CHANGELOG v1.5.1-v1.5.3).

Not meant to be run outside CI — use a real vault for real audits.
"""
import json
import os
import sys
from datetime import datetime, timedelta


def build_fixture(root):
    """Populate `root` with the minimum structure the scripts expect."""
    daily = os.path.join(root, "Daily")
    skills_notes = os.path.join(root, "Skills-Notes")
    memory_review = os.path.join(root, "Memory-Review")
    os.makedirs(daily, exist_ok=True)
    os.makedirs(skills_notes, exist_ok=True)
    os.makedirs(memory_review, exist_ok=True)

    today = datetime.now()
    y, mo, d = today.strftime("%Y"), today.strftime("%m"), today.strftime("%d")
    session_dir = os.path.join(daily, y, mo, d)
    os.makedirs(session_dir, exist_ok=True)

    # One fake archived session, shaped like a real hermes export.
    session_id = "ci-fixture-session-0001"
    session_md = f"""---
session_id: "{session_id}"
title: "CI fixture session"
created_at: "{today.strftime('%Y-%m-%d')}T09:00:00+05:30"
message_count: 4
model_config: '{{"_usage_anchor": {{"prompt_tokens": 120, "completion_tokens": 80}}}}'
---

# CI fixture session

This is a fake session used only to smoke-test Scripts/vault_audit.py
and Scripts/agent_performance.py in CI. Not a real conversation.

```json
[{{"function": {{"name": "read_file"}}}}]
```
"""
    with open(os.path.join(session_dir, f"{session_id}.md"), "w", encoding="utf-8") as f:
        f.write(session_md)

    # Manifest entry matching the session above.
    manifest_path = os.path.join(daily, "manifest.jsonl")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "session_id": session_id,
            "title": "CI fixture session",
            "path": os.path.join(session_dir, f"{session_id}.md"),
            "format": "md",
            "message_count": 4,
            "exported_at": today.timestamp(),
        }) + "\n")

    # A stale Memory-Review entry with an open task, to exercise that check.
    stale_date = today - timedelta(days=45)
    mr_file = os.path.join(memory_review, "ci-fixture-candidate.md")
    with open(mr_file, "w", encoding="utf-8") as f:
        f.write("# CI fixture candidate\n\n- [ ] Review this fake candidate\n")
    stale_ts = stale_date.timestamp()
    os.utime(mr_file, (stale_ts, stale_ts))

    # Minimal token usage log so hourly_archive.py's append path is exercised.
    with open(os.path.join(skills_notes, "Token-Usage.log"), "w", encoding="utf-8") as f:
        f.write("# Token Usage Log\n")

    # An intentionally broken wikilink + one orphan file, to exercise
    # vault_audit.py's detection (and prove it doesn't crash on findings).
    with open(os.path.join(root, "Broken-Link-Test.md"), "w", encoding="utf-8") as f:
        f.write("# Broken link test\n\nSee [[Does Not Exist]] for details.\n")

    print(f"Fixture vault built at {root}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        print("Usage: build_fixture_vault.py <target_dir>")
        sys.exit(1)
    build_fixture(target)
