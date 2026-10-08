#!/usr/bin/env python3
"""
Hermes Brain — one-off migration for issue #10.

v1.23.0 ("separate cron metadata from session content") only moved cron
LOCK/LOG files into 04-Archives/Cron/. The cron-run SESSION NOTES themselves
(cron_<jobid>_<timestamp>-<slug>.md) kept landing in 04-Archives/Daily/,
mixed in with real chat sessions.

This script finds existing cron_*.md files already sitting under Daily/ and
relocates them to 04-Archives/Cron/sessions/, preserving the YYYY/MM/DD
structure, and updates manifest.jsonl so the path stays correct.

Safe to re-run: files already in Cron/sessions/ are skipped, and the going-
forward fix in hermes_session_sync.py routes new cron sessions there
directly, so this only ever needs to run once per vault.

Usage:
    python migrate_cron_sessions.py --vault "<vault-path>" [--dry-run] [--verbose]
"""
import argparse
import json
import os
import re
import shutil
import sys

CRON_PREFIX_RE = re.compile(r"^cron_")


def get_vault(explicit=None):
    if explicit and os.path.isdir(explicit):
        return os.path.abspath(explicit)
    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.isdir(env_vault):
        return os.path.abspath(env_vault)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for cand in [
        os.path.abspath(os.path.join(script_dir, "..", "..")),
        os.path.abspath(os.path.join(script_dir, "..")),
    ]:
        if os.path.isdir(os.path.join(cand, ".obsidian")) or os.path.isdir(
            os.path.join(cand, "01-Projects")
        ):
            return cand
    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def find_cron_notes(daily_dir):
    """Yield (full_path, rel_to_daily) for every cron_*.md under Daily/."""
    for root, dirs, files in os.walk(daily_dir):
        # Don't descend into an already-migrated Cron/ folder if it's
        # somehow nested, and skip hidden dirs.
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if fname.endswith(".md") and CRON_PREFIX_RE.match(fname):
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, daily_dir)
                yield full, rel


def main():
    parser = argparse.ArgumentParser(description="Migrate existing cron session notes out of Daily/ (issue #10)")
    parser.add_argument("--vault", help="Vault root directory path")
    parser.add_argument("--dry-run", action="store_true", help="Show what would move without moving anything")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    vault = get_vault(args.vault)
    daily_cand = os.path.join(vault, "04-Archives", "Daily")
    daily = daily_cand if os.path.isdir(daily_cand) else os.path.join(vault, "Daily")
    cron_sessions_dir = os.path.join(vault, "04-Archives", "Cron", "sessions")

    if not os.path.isdir(daily):
        print(f"No Daily/ folder found at {daily} — nothing to migrate.")
        return 0

    os.makedirs(cron_sessions_dir, exist_ok=True)

    manifest_path = os.path.join(daily, "manifest.jsonl")
    manifest_records = []
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    manifest_records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    path_rewrites = {}  # old_abspath -> new_abspath
    moved = 0
    skipped = 0

    for full_path, rel_path in find_cron_notes(daily):
        new_path = os.path.join(cron_sessions_dir, rel_path)
        if os.path.abspath(full_path) == os.path.abspath(new_path):
            skipped += 1
            continue

        if args.verbose or args.dry_run:
            print(f"{'[DRY RUN] ' if args.dry_run else ''}MOVE: {rel_path}")

        if not args.dry_run:
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            if os.path.exists(new_path):
                os.remove(new_path)  # shouldn't normally happen, but don't crash on re-run
            shutil.move(full_path, new_path)

        path_rewrites[os.path.abspath(full_path)] = os.path.abspath(new_path)
        moved += 1

    # Clean up now-empty YYYY/MM/DD directories left behind in Daily/
    if not args.dry_run:
        for root, dirs, files in os.walk(daily, topdown=False):
            if root == daily:
                continue
            try:
                if not os.listdir(root):
                    os.rmdir(root)
            except OSError:
                pass

    # Rewrite manifest.jsonl paths for the records we moved
    if path_rewrites and manifest_records:
        updated = 0
        for rec in manifest_records:
            p = rec.get("path")
            if p and os.path.abspath(p) in path_rewrites:
                rec["path"] = path_rewrites[os.path.abspath(p)]
                updated += 1
        if updated and not args.dry_run:
            with open(manifest_path, "w", encoding="utf-8") as f:
                for rec in manifest_records:
                    f.write(json.dumps(rec) + "\n")
        if args.verbose:
            verb2 = "Would update" if args.dry_run else "Updated"
            print(f"{verb2} {updated} manifest.jsonl path(s)")

    verb = "Would move" if args.dry_run else "Moved"
    print(f"{verb} {moved} cron session note(s) to 04-Archives/Cron/sessions/ "
          f"({skipped} already in place).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
