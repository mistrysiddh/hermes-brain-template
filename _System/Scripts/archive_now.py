#!/usr/bin/env python3
"""
Hermes Brain — instant session archiver (manual trigger).

Exports Hermes chat sessions active since a given time (default: last 5 minutes)
or by session ID as redacted markdown, reorganizes them into the vault's
Daily/YYYY/MM/DD/ convention, updates manifest.jsonl, and extracts token usage
to Token-Usage.log.

Updates old chats with new messages rather than dropping them.
Uses cross-platform file locking with retry so it never deadlocks on existing lock files.
"""
import argparse
import sys
import os

try:
    from hermes_session_sync import sync_sessions, resolve_vault
except ImportError:
    # Ensure current directory is in sys.path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hermes_session_sync import sync_sessions, resolve_vault


def main():
    parser = argparse.ArgumentParser(description="Instant Hermes session archiver")
    parser.add_argument("--since", default="5m", help="How far back to look (e.g., '5m', '1h', '2h30m')")
    parser.add_argument("--session-id", type=str, help="Specific session ID to archive immediately")
    parser.add_argument("--vault", type=str, help="Vault root directory (overrides auto-detection and HERMES_VAULT_PATH)")
    parser.add_argument("--enrich", action="store_true", help="Run enrichment after archiving")
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    if not vault:
        print("Could not resolve vault path — set HERMES_VAULT_PATH or pass --vault <path>")
        sys.exit(1)

    success = sync_sessions(
        vault_path=vault,
        session_id=args.session_id,
        since=args.since if not args.session_id else None,
        enrich=args.enrich,
        verbose=True,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()