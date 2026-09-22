#!/usr/bin/env python3
"""
Hermes Brain — hourly session archiver + token tracker.

Delegates directly to hermes_session_sync.sync_sessions() to ensure
consistent, database-aware session discovery, stale slug cleanup,
and synchronized locking across cron and manual triggers.
"""
import argparse
import os
import sys

try:
    from hermes_session_sync import sync_sessions, resolve_vault
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hermes_session_sync import sync_sessions, resolve_vault


def main():
    parser = argparse.ArgumentParser(description="Hermes Brain hourly session archiver + token tracker")
    parser.add_argument("--vault", type=str, help="Vault root directory (overrides auto-detection and HERMES_VAULT_PATH)")
    parser.add_argument("--enrich", action="store_true", help="Run session enrichment after archiving to add glanceable summaries")
    parser.add_argument("--since", type=str, help="Export sessions since this duration (e.g. '70m', '2h'). If omitted, uses manifest-aware window")
    parser.add_argument("--tag", action="store_true", help="Run session tagger after archiving")
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    if not vault:
        print("Could not resolve vault path — set HERMES_VAULT_PATH or pass --vault <path>")
        sys.exit(1)

    success = sync_sessions(
        vault_path=vault,
        since=args.since,
        enrich=args.enrich,
        tag=args.tag,
        verbose=True,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()