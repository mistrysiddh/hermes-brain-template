#!/usr/bin/env python3
"""
Hermes Brain — hourly session archiver + token tracker.

Exports Hermes chat sessions active in the last hour as redacted markdown,
reorganizes them into the vault's Daily/YYYY/MM/DD/ convention, maintains
a deduplicated manifest.jsonl, AND extracts token usage from JSONL export
to maintain a running total in Skills-Notes/Token-Usage.log.

Only ONE cron job should ever run this against a given vault, to avoid
manifest.jsonl races (see Daily/README.md).

Optional: --enrich flag runs session enrichment after archiving to add
glanceable summaries to session files (calls enrich_session.py internally).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import argparse
from datetime import datetime

# Cross-platform locking
try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False

def resolve_vault(explicit_vault=None):
    """Resolve the vault root path from argument, script location, or environment."""
    if explicit_vault and os.path.isdir(explicit_vault):
        return os.path.abspath(explicit_vault)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cand_para = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if os.path.exists(os.path.join(cand_para, ".obsidian")) or os.path.exists(os.path.join(cand_para, "01-Projects")):
        return cand_para
    cand_flat = os.path.abspath(os.path.join(script_dir, ".."))
    if os.path.exists(os.path.join(cand_flat, ".obsidian")) or os.path.exists(os.path.join(cand_flat, "01-Projects")):
        return cand_flat
    env_vault = os.environ.get("HERMES_VAULT_PATH")
    if env_vault and os.path.exists(env_vault):
        return os.path.abspath(env_vault)
    return None


VAULT = None
DAILY = None
MANIFEST = None
TOKEN_LOG = None
LOCK_FILE = None


def init_vault_paths(vault_path):
    """Initialize global path variables for the given vault."""
    global VAULT, DAILY, MANIFEST, TOKEN_LOG, LOCK_FILE
    VAULT = vault_path
    daily_cand = os.path.join(VAULT, "04-Archives", "Daily")
    DAILY = daily_cand if os.path.exists(daily_cand) else os.path.join(VAULT, "Daily")
    os.makedirs(DAILY, exist_ok=True)
    MANIFEST = os.path.join(DAILY, "manifest.jsonl")

    token_cand = os.path.join(VAULT, "04-Archives", "Audit-Reports", "Token-Usage.log")
    TOKEN_LOG = token_cand if os.path.exists(os.path.dirname(token_cand)) else os.path.join(VAULT, "Skills-Notes", "Token-Usage.log")
    LOCK_FILE = os.path.join(DAILY, ".hourly_archive.lock")


# Initialize default vault if discoverable
_initial_vault = resolve_vault()
if _initial_vault:
    init_vault_paths(_initial_vault)

CREATED_RE = re.compile(r'created_at:\s*"(\d{4})-(\d{2})-(\d{2})')



def acquire_lock():
    """Acquire an exclusive lock to prevent concurrent execution (cross-platform)."""
    global _lock_handle
    try:
        # Ensure lock file exists
        os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
        with open(LOCK_FILE, "a"):
            pass
        
        _lock_handle = open(LOCK_FILE, "r+")
        if HAS_PORTALOCKER:
            portalocker.lock(_lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        else:
            # Fallback: fcntl on Unix, msvcrt on Windows
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(_lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(_lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError, ImportError):
        # Lock already held or locking failed
        if _lock_handle:
            try:
                _lock_handle.close()
            except Exception:
                pass
            _lock_handle = None
        return False
    except Exception as e:
        print(f"Failed to acquire lock: {e}")
        if _lock_handle:
            try:
                _lock_handle.close()
            except Exception:
                pass
            _lock_handle = None
        return False


def release_lock():
    """Release the lock by unlocking and closing the handle."""
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
        except Exception as e:
            print(f"Warning: Failed to unlock: {e}")
        try:
            _lock_handle.close()
        except Exception:
            pass
        _lock_handle = None


def find_hermes():
    for cand in ("hermes", shutil.which("hermes")):
        if cand and shutil.which(cand):
            return cand
    return "hermes"


def extract_tokens_from_jsonl(jsonl_path):
    """Parse JSONL export and sum prompt+completion tokens per session.
    
    Supports multiple token usage formats across Hermes versions:
    - model_config._usage_anchor (legacy)
    - model_config.usage
    - usage (top-level)
    - token_usage (top-level)
    """
    total = 0
    sessions = 0
    sessions_with_tokens = 0
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
            
            # Try multiple extraction paths in order of preference
            session_tokens = None
            
            # Path 1: model_config._usage_anchor (legacy)
            model_config = rec.get("model_config", "")
            if model_config:
                try:
                    cfg = json.loads(model_config)
                    usage = cfg.get("_usage_anchor", {})
                    if usage:
                        prompt = usage.get("prompt_tokens", 0)
                        completion = usage.get("completion_tokens", 0)
                        session_tokens = prompt + completion
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Path 2: model_config.usage
            if session_tokens is None and model_config:
                try:
                    cfg = json.loads(model_config)
                    usage = cfg.get("usage", {})
                    if usage:
                        prompt = usage.get("prompt_tokens", 0)
                        completion = usage.get("completion_tokens", 0)
                        session_tokens = prompt + completion
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Path 3: top-level usage
            if session_tokens is None:
                usage = rec.get("usage", {})
                if usage:
                    prompt = usage.get("prompt_tokens", 0)
                    completion = usage.get("completion_tokens", 0)
                    session_tokens = prompt + completion
            
            # Path 4: top-level token_usage
            if session_tokens is None:
                usage = rec.get("token_usage", {})
                if usage:
                    prompt = usage.get("prompt_tokens", 0)
                    completion = usage.get("completion_tokens", 0)
                    session_tokens = prompt + completion
            
            if session_tokens is not None:
                total += session_tokens
                sessions_with_tokens += 1
            sessions += 1
    
    # Log warning if some sessions lacked token data
    if sessions > 0 and sessions_with_tokens == 0:
        print("Warning: No token usage data found in any session — check Hermes version compatibility")
    elif sessions > 0 and sessions_with_tokens < sessions:
        print(f"Warning: Only {sessions_with_tokens}/{sessions} sessions had token usage data")
    
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
    parser = argparse.ArgumentParser(description="Hermes Brain hourly session archiver + token tracker")
    parser.add_argument("--vault", type=str, help="Vault root directory (overrides auto-detection and HERMES_VAULT_PATH)")
    parser.add_argument("--enrich", action="store_true", help="Run session enrichment after archiving to add glanceable summaries")
    parser.add_argument("--since", type=str, help="Export sessions since this timestamp (ISO format). If omitted, reads latest exported_at from manifest.jsonl")
    parser.add_argument("--tag", action="store_true", help="Run session tagger after archiving (default: off, run separately via cron)")
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    if not vault:
        print("Could not resolve vault path — set HERMES_VAULT_PATH or pass --vault <path>")
        sys.exit(1)
    init_vault_paths(vault)

    # 0. Acquire exclusive lock to prevent concurrent execution
    if not acquire_lock():
        print("Another instance of hourly_archive.py is already running — exiting.")
        sys.exit(0)


    try:
        hermes_bin = find_hermes()

        # Determine the "since" timestamp for export
        since_arg = "70m"  # default fallback
        if args.since:
            since_arg = args.since
        elif os.path.exists(MANIFEST):
            # Read latest exported_at from manifest
            try:
                latest_exported = 0
                with open(MANIFEST, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                            exported_at = rec.get("exported_at", 0)
                            if exported_at and exported_at > latest_exported:
                                latest_exported = exported_at
                        except json.JSONDecodeError:
                            continue
                if latest_exported > 0:
                    # Convert to ISO format for --newer-than (if Hermes supports it)
                    # Otherwise use relative time from now
                    since_seconds = int(datetime.now().timestamp() - latest_exported)
                    if since_seconds > 0:
                        since_arg = f"{since_seconds}s"
                    print(f"Using manifest-based since: {since_arg} (last export at {datetime.fromtimestamp(latest_exported).isoformat()})")
            except Exception as e:
                print(f"Warning: Could not read manifest for since timestamp: {e}")

        # 1. Export sessions as markdown (for the vault) — existing behavior
        cmd_md = [
            hermes_bin, "sessions", "export",
            "--format", "md",
            "--newer-than", since_arg,
            "--redact",
            "--yes",
            DAILY,
        ]
        result_md = subprocess.run(cmd_md, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result_md.stdout:
            print(result_md.stdout.strip())
        if result_md.returncode != 0:
            if result_md.stderr:
                print(result_md.stderr.strip())
            sys.exit(result_md.returncode)

        if result_md.stdout and "Exported 0 session" in result_md.stdout:
            print("No new sessions this hour.")
            return

        # 2. ALSO export as JSONL to capture token usage (streaming to stdout)
        cmd_jsonl = [
            hermes_bin, "sessions", "export",
            "--format", "jsonl",
            "--newer-than", since_arg,
            "--redact",
            "--yes",
            "-",  # stdout
        ]
        result_jsonl = subprocess.run(cmd_jsonl, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result_jsonl.returncode != 0 or not result_jsonl.stdout:
            print(f"Warning: JSONL export failed: {(result_jsonl.stderr or '').strip()}")
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

        # 7. Optional: Run session tagger if --tag flag is set (default: off, run separately via cron)
        if args.tag:
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join(os.path.dirname(__file__), "session_tagger.py")],
                    capture_output=True, text=True, timeout=120
                )
                if result.stdout:
                    print(result.stdout.strip())
                if result.stderr:
                    print(f"Tagger warning: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print("Warning: session_tagger.py timed out")
            except Exception as e:
                print(f"Warning: session_tagger.py failed: {e}")

        # 8. Optional: Run session enrichment if --enrich flag is set
        if args.enrich:
            try:
                enrich_script = os.path.join(os.path.dirname(__file__), "enrich_session.py")
                if os.path.exists(enrich_script):
                    result = subprocess.run(
                        [sys.executable, enrich_script],
                        capture_output=True, text=True, timeout=120
                    )
                    if result.stdout:
                        print(result.stdout.strip())
                    if result.stderr:
                        print(f"Enrichment warning: {result.stderr.strip()}")
                else:
                    print("Warning: enrich_session.py not found, skipping enrichment")
            except subprocess.TimeoutExpired:
                print("Warning: enrich_session.py timed out")
            except Exception as e:
                print(f"Warning: enrich_session.py failed: {e}")

    finally:
        release_lock()


if __name__ == "__main__":
    main()