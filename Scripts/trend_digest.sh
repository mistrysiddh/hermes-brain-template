#!/usr/bin/env bash
# trend_digest.sh — Linux/macOS port of New-TrendDigest.ps1 / Write-TrendDigest.ps1.
# Uses trend_digest.py (sentence-transformers) instead of Ollama.
# Usage: ./trend_digest.sh [vault_path] [query] [top_n]
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
VAULT="${1:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
QUERY="${2:-local LLM agents offline}"
TOP_N="${3:-8}"
OUT_DIR="$VAULT/Research/Trend-Digest"
mkdir -p "$OUT_DIR"

# Prefer a Hermes-managed venv if present, else fall back to python3/python on PATH.
CANDIDATES=(
  "$HOME/.local/share/hermes/hermes-agent/venv/bin/python"
  "$HOME/Library/Application Support/hermes/hermes-agent/venv/bin/python"
)
PY=""
for c in "${CANDIDATES[@]}"; do
  if [ -x "$c" ]; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  PY=$(command -v python3 || command -v python || true)
fi
if [ -z "$PY" ]; then
  echo "No python interpreter found on PATH." >&2
  exit 1
fi

if ! "$PY" -c "import sentence_transformers" >/dev/null 2>&1; then
  echo "sentence-transformers not installed for $PY." >&2
  echo "Install it with: $PY -m pip install sentence-transformers numpy" >&2
  exit 1
fi

NOTES_JSON=$("$PY" "$SCRIPT_DIR/trend_digest.py" "$VAULT" "$QUERY" "$TOP_N")

TODAY=$(date +%Y-%m-%d)
OUT_FILE="$OUT_DIR/$TODAY.md"

"$PY" - "$NOTES_JSON" "$QUERY" "$TODAY" "$OUT_FILE" <<'PYEOF'
import sys, json
notes_json, query, today, out_file = sys.argv[1:5]
notes = json.loads(notes_json)
if not notes:
    print("No notes returned — check the vault path is correct and contains .md files.", file=sys.stderr)
    sys.exit(1)
with open(out_file, "w", encoding="utf-8") as f:
    f.write(f"# Trend Digest - {today}\n## Query: {query}\n| Score | Note | Snippet |\n|-------|------|---------|\n")
    for n in notes:
        f.write(f"| {n['score']:.4f} | [[{n['path']}]] | {n['snippet']} |\n")
print(f"Digest written to {out_file}")
PYEOF
