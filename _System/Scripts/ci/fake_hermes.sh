#!/usr/bin/env bash
# Minimal fake `hermes` CLI for CI smoke-testing hourly_archive.py.
# Only implements the `sessions export` subcommand shape the script uses;
# everything else is out of scope for this stub.
set -euo pipefail

if [[ "${1:-}" == "sessions" && "${2:-}" == "export" ]]; then
  fmt=""
  dest=""
  args=("$@")
  for ((i = 0; i < ${#args[@]}; i++)); do
    if [[ "${args[$i]}" == "--format" ]]; then
      fmt="${args[$((i + 1))]}"
    fi
  done
  dest="${args[-1]}"

  if [[ "$fmt" == "md" ]]; then
    # "Exported 0 sessions" short-circuits the real script — return that
    # so the smoke test exercises the no-op path cleanly and deterministically.
    echo "Exported 0 sessions."
    exit 0
  elif [[ "$fmt" == "jsonl" ]]; then
    # No stdout needed since the md export above already reported 0.
    exit 0
  fi
fi

echo "fake-hermes: unhandled args: $*" >&2
exit 1
