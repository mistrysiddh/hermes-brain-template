#!/usr/bin/env python3
"""
Hermes Brain — session synchronizer & archiver.

Handles:
1. Lifecycle hooks:
   - on_session_start: creates the session note in 04-Archives/Daily/YYYY/MM/DD/ as soon as chat starts.
   - post_llm_call: updates the session note after each turn in an ongoing chat.
   - on_session_end / on_session_finalize: updates the session note with complete chat and tokens on completion.
2. Manual triggers (archive_now):
   - python hermes_session_sync.py --since 1h
   - python hermes_session_sync.py --session-id <id>
3. Hourly archiving cron jobs:
   - python hermes_session_sync.py

Ensures:
- Old chats are updated with new messages rather than dropped.
- Database-aware session discovery from Hermes state.db so active sessions (ended_at IS NULL) are never missed.
- Lock file uses real cross-platform file locking with retry timeout.
- Old slugs are cleaned up if a session title is updated.
- Manifest and token logs are properly kept in sync.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False

_lock_handle = None
CREATED_RE = re.compile(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})')


def resolve_vault(explicit_vault=None):
    """Resolve vault root path from parameter, environment, or relative directory traversal."""
    if explicit_vault and os.path.isdir(explicit_vault):
        return os.path.abspath(explicit_vault)
    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.isdir(env_vault):
        return os.path.abspath(env_vault)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cand_para = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if os.path.exists(os.path.join(cand_para, ".obsidian")) or os.path.exists(os.path.join(cand_para, "01-Projects")):
        return cand_para
    cand_flat = os.path.abspath(os.path.join(script_dir, ".."))
    if os.path.exists(os.path.join(cand_flat, ".obsidian")) or os.path.exists(os.path.join(cand_flat, "01-Projects")):
        return cand_flat
    return None


def init_vault_paths(vault_path):
    daily_cand = os.path.join(vault_path, "04-Archives", "Daily")
    daily = daily_cand if os.path.exists(daily_cand) else os.path.join(vault_path, "Daily")
    os.makedirs(daily, exist_ok=True)
    manifest = os.path.join(daily, "manifest.jsonl")

    audit_dir = os.path.join(vault_path, "04-Archives", "Audit-Reports")
    if os.path.exists(audit_dir):
        token_log = os.path.join(audit_dir, "Token-Usage.log")
    else:
        token_log = os.path.join(vault_path, "Skills-Notes", "Token-Usage.log")

    lock_file = os.path.join(daily, ".hourly_archive.lock")
    return vault_path, daily, manifest, token_log, lock_file


def acquire_lock(lock_file, timeout_seconds=5.0):
    """Acquire an exclusive lock with retry timeout (cross-platform)."""
    global _lock_handle
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    start_time = time.time()

    while True:
        try:
            with open(lock_file, "a"):
                pass
            _lock_handle = open(lock_file, "r+")
            if HAS_PORTALOCKER:
                portalocker.lock(_lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
            else:
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(_lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(_lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError, ImportError):
            if _lock_handle:
                try:
                    _lock_handle.close()
                except Exception:
                    pass
                _lock_handle = None
            if time.time() - start_time >= timeout_seconds:
                return False
            time.sleep(0.2)
        except Exception:
            if _lock_handle:
                try:
                    _lock_handle.close()
                except Exception:
                    pass
                _lock_handle = None
            return False


def release_lock():
    """Release the lock handle."""
    global _lock_handle
    if _lock_handle:
        try:
            if HAS_PORTALOCKER:
                portalocker.unlock(_lock_handle)
            else:
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(_lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(_lock_handle.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            _lock_handle.close()
        except Exception:
            pass
        _lock_handle = None


def find_hermes():
    candidates = [
        "hermes",
        shutil.which("hermes"),
        os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe"),
        os.path.expanduser("~/.local/bin/hermes"),
        os.path.expanduser("~/bin/hermes"),
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            return os.path.abspath(cand)
        if cand and shutil.which(cand):
            return cand
    return "hermes"


def find_hermes_db():
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\hermes\state.db"),
        os.path.expanduser("~/.hermes/state.db"),
        os.path.expanduser("~/.local/share/hermes/state.db"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return os.path.abspath(c)
    return None


def get_active_session_ids_from_db(since_seconds=3600, db_path=None):
    if not db_path:
        db_path = find_hermes_db()
    if not db_path or not os.path.exists(db_path):
        return []
    import sqlite3
    cutoff = time.time() - since_seconds
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM sessions 
            WHERE COALESCE(last_activity_at, started_at, 0) >= ?
            ORDER BY COALESCE(last_activity_at, started_at, 0) ASC
        """, (cutoff,))
        return [row[0] for row in cur.fetchall()]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def extract_tokens_from_jsonl(jsonl_path):
    total = 0
    sessions = 0
    if not os.path.exists(jsonl_path):
        return total, sessions
    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_tokens = None
            model_config = rec.get("model_config", "")
            if model_config and isinstance(model_config, str):
                try:
                    cfg = json.loads(model_config)
                    usage = cfg.get("_usage_anchor") or cfg.get("usage") or {}
                    if usage:
                        prompt = usage.get("prompt_tokens", 0) or 0
                        completion = usage.get("completion_tokens", 0) or 0
                        session_tokens = prompt + completion
                except (json.JSONDecodeError, TypeError):
                    pass

            if session_tokens is None:
                usage = rec.get("usage") or rec.get("token_usage") or {}
                if isinstance(usage, dict) and usage:
                    prompt = usage.get("prompt_tokens", 0) or 0
                    completion = usage.get("completion_tokens", 0) or 0
                    session_tokens = prompt + completion

            if session_tokens is not None:
                total += session_tokens
            sessions += 1
    return total, sessions


def update_token_log(token_log_path, daily_total, session_count):
    if daily_total <= 0:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    line = f"{today}: {daily_total} tokens ({session_count} session(s))\n"
    os.makedirs(os.path.dirname(token_log_path), exist_ok=True)
    with open(token_log_path, "a", encoding="utf-8") as f:
        f.write(line)


def parse_since_arg(since_str):
    if not since_str:
        return 300
    total_seconds = 0
    matches = re.findall(r'(\d+)([smhd])', since_str.lower())
    for value, unit in matches:
        val = int(value)
        if unit == 's':
            total_seconds += val
        elif unit == 'm':
            total_seconds += val * 60
        elif unit == 'h':
            total_seconds += val * 3600
        elif unit == 'd':
            total_seconds += val * 86400
    if total_seconds == 0:
        try:
            return int(since_str) * 60
        except ValueError:
            return 300
    return total_seconds


def sync_sessions(vault_path=None, session_id=None, since=None, enrich=False, tag=False, verbose=False):
    """
    Core sync execution:
    Exports from Hermes, reorganizes into Daily/YYYY/MM/DD/,
    updates existing session notes, and maintains manifest.jsonl.
    """
    vault = resolve_vault(vault_path)
    if not vault:
        if verbose:
            print("Could not resolve vault path.")
        return False

    vault, daily, manifest, token_log, lock_file = init_vault_paths(vault)

    if not acquire_lock(lock_file, timeout_seconds=5.0):
        if verbose:
            print("Another archive process holds the lock — skipping.")
        return False

    try:
        hermes_bin = find_hermes()

        # Build list of sessions to export
        session_ids_to_export = []
        if session_id:
            session_ids_to_export = [session_id]
        else:
            since_seconds = parse_since_arg(since) if since else 4200
            if not since and os.path.exists(manifest):
                try:
                    latest_exported = 0
                    with open(manifest, encoding="utf-8") as f:
                        for line in f:
                            l = line.strip()
                            if not l:
                                continue
                            try:
                                rec = json.loads(l)
                                exp = rec.get("exported_at", 0)
                                if exp and exp > latest_exported:
                                    latest_exported = exp
                            except json.JSONDecodeError:
                                continue
                    if latest_exported > 0:
                        diff = int(time.time() - latest_exported)
                        since_seconds = max(diff + 600, 1800)
                except Exception:
                    pass

            db_sids = get_active_session_ids_from_db(since_seconds=since_seconds)
            if db_sids:
                session_ids_to_export = db_sids

        # 1. Export Markdown & JSONL
        total_tokens = 0
        token_sessions = 0

        if session_ids_to_export:
            for sid in session_ids_to_export:
                cmd_md = [
                    hermes_bin, "sessions", "export",
                    "--format", "md",
                    "--session-id", sid,
                    "--force",
                    "--redact",
                    "--yes",
                    daily,
                ]
                res_md = subprocess.run(cmd_md, capture_output=True, text=True, encoding="utf-8", errors="replace")
                if verbose and res_md.stdout:
                    print(res_md.stdout.strip())

                cmd_jsonl = [
                    hermes_bin, "sessions", "export",
                    "--format", "jsonl",
                    "--session-id", sid,
                    "--force",
                    "--redact",
                    "--yes",
                    "-",
                ]
                res_jsonl = subprocess.run(cmd_jsonl, capture_output=True, text=True, encoding="utf-8", errors="replace")
                if res_jsonl.returncode == 0 and res_jsonl.stdout and res_jsonl.stdout.strip():
                    jsonl_path = os.path.join(daily, f"tmp_{sid}.jsonl")
                    with open(jsonl_path, "w", encoding="utf-8") as f:
                        f.write(res_jsonl.stdout)
                    t_tokens, t_sess = extract_tokens_from_jsonl(jsonl_path)
                    total_tokens += t_tokens
                    token_sessions += t_sess
                    try:
                        os.remove(jsonl_path)
                    except OSError:
                        pass
        else:
            since_arg = since or "70m"
            cmd_md = [
                hermes_bin, "sessions", "export",
                "--format", "md",
                "--newer-than", since_arg,
                "--force",
                "--redact",
                "--yes",
                daily,
            ]
            cmd_jsonl = [
                hermes_bin, "sessions", "export",
                "--format", "jsonl",
                "--newer-than", since_arg,
                "--force",
                "--redact",
                "--yes",
                "-",
            ]
            res_md = subprocess.run(cmd_md, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if verbose and res_md.stdout:
                print(res_md.stdout.strip())
            res_jsonl = subprocess.run(cmd_jsonl, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res_jsonl.returncode == 0 and res_jsonl.stdout and res_jsonl.stdout.strip():
                jsonl_path = os.path.join(daily, "tmp_export.jsonl")
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    f.write(res_jsonl.stdout)
                total_tokens, token_sessions = extract_tokens_from_jsonl(jsonl_path)
                try:
                    os.remove(jsonl_path)
                except OSError:
                    pass

        if total_tokens > 0:
            update_token_log(token_log, total_tokens, token_sessions)

        # 3. Load existing manifest
        existing = {}
        if os.path.exists(manifest):
            with open(manifest, encoding="utf-8", errors="replace") as f:
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

        # 4. Reorganize flat markdown files in Daily into Daily/YYYY/MM/DD/
        scaffolding = {"README.md", "Timeline.md", "Chat-Correlation.md", "tmp_export.jsonl"}
        moved_count = 0

        for fname in os.listdir(daily):
            fpath = os.path.join(daily, fname)
            if not os.path.isfile(fpath) or not fname.endswith(".md") or fname in scaffolding:
                continue

            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    head = f.read(4000)
            except Exception:
                continue

            m = CREATED_RE.search(head)
            if not m:
                continue
            y, mo, d = m.groups()

            sid_m = re.search(r'session_id:\s*"([^"]+)"', head)
            sid = sid_m.group(1) if sid_m else None

            destdir = os.path.join(daily, y, mo, d)
            os.makedirs(destdir, exist_ok=True)
            destpath = os.path.join(destdir, fname)

            # If this session previously existed under a different filename (e.g. title slug updated), remove old file
            if sid and sid in existing:
                old_path = existing[sid].get("path")
                if (
                    old_path
                    and os.path.exists(old_path)
                    and os.path.abspath(old_path) != os.path.abspath(destpath)
                    and os.path.abspath(old_path) != os.path.abspath(fpath)
                ):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            # Also clean up any duplicate/stale files for this session_id in destdir (e.g. <sid>-session.md or previous title)
            if sid and os.path.isdir(destdir):
                for existing_f in os.listdir(destdir):
                    if existing_f.endswith(".md") and (existing_f.startswith(f"{sid}-") or existing_f == f"{sid}.md"):
                        if existing_f != fname:
                            try:
                                os.remove(os.path.join(destdir, existing_f))
                            except OSError:
                                pass

            # Move or replace file into destination
            if os.path.abspath(fpath) != os.path.abspath(destpath):
                if os.path.exists(destpath):
                    os.replace(fpath, destpath)  # Overwrite existing with updated content
                else:
                    shutil.move(fpath, destpath)
                moved_count += 1

            # Update manifest record
            if sid:
                title_m = re.search(r'title:\s*"([^"]*)"', head)
                msgcount_m = re.search(r"message_count:\s*(\d+)", head)
                existing[sid] = {
                    "session_id": sid,
                    "title": title_m.group(1) if title_m else "",
                    "path": destpath,
                    "format": "md",
                    "message_count": int(msgcount_m.group(1)) if msgcount_m else None,
                    "exported_at": os.path.getmtime(destpath),
                }

        # 5. Rewrite manifest sorted by exported_at
        records = sorted(existing.values(), key=lambda r: r.get("exported_at") or 0)
        with open(manifest, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

        if verbose:
            print(f"Sync complete: {moved_count} file(s) updated, manifest now has {len(records)} session(s).")

        # 6. Optional enrichment
        if enrich:
            enrich_script = os.path.join(vault, "_System", "Scripts", "enrich_session.py")
            if os.path.exists(enrich_script):
                subprocess.run([sys.executable, enrich_script], capture_output=True, timeout=60)

        # 7. Optional tagging
        if tag:
            tagger_script = os.path.join(vault, "_System", "Scripts", "session_tagger.py")
            if os.path.exists(tagger_script):
                subprocess.run([sys.executable, tagger_script], capture_output=True, timeout=120)

        return True
    finally:
        release_lock()


def main():
    parser = argparse.ArgumentParser(description="Hermes Brain session sync & hook handler")
    parser.add_argument("--session-id", type=str, help="Specific session ID to sync immediately")
    parser.add_argument("--hook", action="store_true", help="Invoked as a Hermes shell hook")
    parser.add_argument("--event", type=str, help="Hook event name (e.g. on_session_start, on_session_end, post_llm_call)")
    parser.add_argument("--since", type=str, help="Lookback time (e.g. '5m', '1h')")
    parser.add_argument("--vault", type=str, help="Vault root directory path")
    parser.add_argument("--enrich", action="store_true", help="Run enrichment after sync")
    parser.add_argument("--tag", action="store_true", help="Run tagger after sync")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output")
    args = parser.parse_args()

    session_id = args.session_id
    # Read from stdin if explicitly invoked as a hook, with a timeout so it never hangs
    if not session_id and (args.hook or args.event):
        import threading
        stdin_holder = [""]

        def _read_stdin():
            try:
                stdin_holder[0] = sys.stdin.read().strip()
            except Exception:
                pass

        t = threading.Thread(target=_read_stdin, daemon=True)
        t.start()
        t.join(timeout=0.5)

        if stdin_holder[0]:
            try:
                data = json.loads(stdin_holder[0])
                session_id = data.get("session_id")
            except Exception:
                pass

    try:
        sync_sessions(
            vault_path=args.vault,
            session_id=session_id,
            since=args.since,
            enrich=args.enrich,
            tag=args.tag,
            verbose=args.verbose or bool(args.since or args.session_id),
        )
    except Exception as e:
        import traceback
        if args.verbose or not (args.hook or args.event):
            traceback.print_exc()
    sys.exit(0)


if __name__ == "__main__":
    main()
