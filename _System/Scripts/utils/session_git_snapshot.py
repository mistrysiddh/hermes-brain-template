#!/usr/bin/env python3
"""
Hermes Brain — Local Session-End Git Snapshot.

Commits a snapshot of the vault to a LOCAL git repository after a session
ends — nothing is ever pushed anywhere by this script. It is a cheap undo
button, not a publishing mechanism.

Why this exists:
Agents editing a vault can make a bad multi-file edit (wrong find/replace,
a note accidentally overwritten, a folder restructure that goes wrong). If
the vault's own local history is a thin layer on top of a git repo that
occasionally gets `git push`ed to GitHub, this script gives you per-session
commits you can `git diff`/`git revert` *before* anything public is touched.

Safety rules:
- NEVER pushes, fetches, or touches any remote. Local commits only.
- Refuses to commit if a secret-looking pattern is detected in the diff
  (API keys, tokens, "password=", AWS/OpenAI/Anthropic key shapes, etc.)
  and instead logs the offending file paths (not their contents) to
  04-Archives/Cron/cron-errors.log so you can clean them up by hand.
- Initializes a local-only git repo on first run if one doesn't exist yet
  (does NOT touch a pre-existing repo's remotes/config).
- Skips cleanly (no error) if git isn't installed, or if there is nothing
  to commit.

Usage:
    python session_git_snapshot.py --vault "<vault-path>" --session-id <id>

Wire this in as a Hermes hook on on_session_end / on_session_finalize,
same pattern as hermes_session_sync.py --hook --event on_session_end.
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Vault resolution (same convention as the other _System/Scripts tools)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Secret scanning — conservative patterns, false positives are fine (they
# just mean "skip the auto-commit, handle it yourself"), false negatives
# are not.
# ---------------------------------------------------------------------------

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),            # OpenAI-style
    re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"),       # Anthropic-style
    re.compile(r"ghp_[a-zA-Z0-9]{30,}"),             # GitHub PAT
    re.compile(r"AKIA[0-9A-Z]{16}"),                 # AWS access key id
    re.compile(r"xox[baprs]-[a-zA-Z0-9\-]{10,}"),   # Slack token
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[=:]\s*['\"]?[A-Za-z0-9/_\-+]{12,}"),
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----"),
]


def scan_file_for_secrets(path):
    """Return True if the file looks like it contains a secret."""
    try:
        if os.path.getsize(path) > 2_000_000:  # skip huge/binary-ish files
            return False
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    return any(p.search(content) for p in SECRET_PATTERNS)


# ---------------------------------------------------------------------------
# Git helpers (local-only — never touches a remote)
# ---------------------------------------------------------------------------

def run_git(vault, *args, check=True):
    return subprocess.run(
        ["git", "-C", vault] + list(args),
        capture_output=True,
        text=True,
        check=check,
    )


def ensure_local_repo(vault):
    """Initialize a git repo if none exists. Never touches an existing one's remotes."""
    result = subprocess.run(
        ["git", "-C", vault, "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True  # already a repo

    init = subprocess.run(
        ["git", "-C", vault, "init"], capture_output=True, text=True
    )
    return init.returncode == 0


def get_changed_files(vault):
    result = run_git(vault, "status", "--porcelain", check=False)
    if result.returncode != 0:
        return []
    files = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        files.append(path)
    return files


def log_error(vault, message):
    cron_dir = os.path.join(vault, "04-Archives", "Cron")
    os.makedirs(cron_dir, exist_ok=True)
    error_log = os.path.join(cron_dir, "cron-errors.log")
    with open(error_log, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | session_git_snapshot | {message}\n")


def log_run(vault, status, detail):
    cron_dir = os.path.join(vault, "04-Archives", "Cron")
    os.makedirs(cron_dir, exist_ok=True)
    run_log = os.path.join(cron_dir, "git-snapshot.log")
    with open(run_log, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {status} | {detail}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Local session-end git snapshot (never pushes)")
    parser.add_argument("--vault", help="Vault root directory path")
    parser.add_argument("--session-id", default=None, help="Session id to tag the commit with")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    vault = get_vault(args.vault)

    # git must exist
    if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
        if args.verbose:
            print("git not found — skipping snapshot (not an error)")
        return 0

    if not ensure_local_repo(vault):
        log_error(vault, "failed to initialize local git repo")
        return 1

    changed = get_changed_files(vault)
    if not changed:
        if args.verbose:
            print("Nothing to snapshot — working tree clean")
        return 0

    # Secret scan every changed/new file before staging anything
    suspicious = []
    for rel_path in changed:
        full_path = os.path.join(vault, rel_path)
        if os.path.isfile(full_path) and scan_file_for_secrets(full_path):
            suspicious.append(rel_path)

    if suspicious:
        log_error(
            vault,
            f"snapshot SKIPPED — possible secret detected in: {', '.join(suspicious)}",
        )
        if args.verbose:
            print(f"⚠️  Skipping snapshot — possible secret in: {suspicious}")
        return 1

    run_git(vault, "add", "-A", check=False)

    label = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    message = f"session snapshot: {label}"
    commit = run_git(vault, "commit", "-m", message, check=False)

    if commit.returncode == 0:
        log_run(vault, "SUCCESS", f"{len(changed)} files | session={label}")
        if args.verbose:
            print(f"✅ Committed snapshot ({len(changed)} files): {message}")
        return 0
    else:
        # Likely "nothing to commit" after staging (e.g. only ignored files changed)
        log_run(vault, "NOOP", commit.stdout.strip()[:200])
        if args.verbose:
            print("Nothing committed (likely all changes were git-ignored)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
