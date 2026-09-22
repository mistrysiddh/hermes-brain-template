#!/usr/bin/env bash
# Hermes Brain — session synchronizer wrapper for Linux/macOS shell hooks
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/hermes_session_sync.py" "$@"
exit 0
