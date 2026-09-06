#!/usr/bin/env bash
# pipeline.sh — daily trend digest via Ollama embeddings (no sentence-transformers needed)
# Linux/macOS port of pipeline.ps1. Resolves the vault as "this script's parent dir's parent"
# (Scripts/.. = vault root) unless overridden.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
VAULT="${1:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
QUERY="${2:-local LLM agents offline}"
TOP_N="${3:-5}"
OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"
OUT_DIR="$VAULT/Research/Trend-Digest"

command -v curl >/dev/null 2>&1 || { echo "curl is required" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }
PY=$(command -v python3 || command -v python)

if ! curl -sf "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
  echo "Warning: can't reach Ollama at $OLLAMA_HOST — is 'ollama serve' running?" >&2
fi

mkdir -p "$OUT_DIR"

# Delegate the actual embedding/ranking work to a small inline Python helper
# (keeps this identical in spirit to pipeline.ps1's embedded script).
"$PY" - "$VAULT" "$QUERY" "$TOP_N" "$OLLAMA_HOST" "$EMBED_MODEL" "$OUT_DIR" <<'PYEOF'
import sys, os, json, math, urllib.request
from datetime import date

vault, query, top_n, ollama_host, embed_model, out_dir = sys.argv[1:7]
top_n = int(top_n)

def embed(text):
    payload = json.dumps({"model": embed_model, "prompt": text}).encode()
    req = urllib.request.Request(f"{ollama_host}/api/embeddings", data=payload,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["embedding"]

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0

notes = []
for root, _, files in os.walk(vault):
    if os.sep + "." in root + os.sep:
        continue
    for f in files:
        if f.lower().endswith(".md"):
            notes.append(os.path.join(root, f))

if not notes:
    print(f"No markdown notes found in {vault}", file=sys.stderr)
    sys.exit(1)

print(f"Found {len(notes)} notes. Computing embeddings (this may take a while)...")
q_emb = embed(query)

results = []
for path in notes:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        if not content.strip():
            continue
        emb = embed(content)
        score = cosine(q_emb, emb)
        rel = os.path.relpath(path, vault).replace("\\", "/")
        snippet = content[:200].replace("\r\n", " ").replace("\n", " ")
        results.append((score, rel, snippet))
    except Exception as e:
        print(f"Warning: failed to process {path}: {e}", file=sys.stderr)

results.sort(key=lambda r: r[0], reverse=True)
top = results[:top_n]

today = date.today().isoformat()
out_file = os.path.join(out_dir, f"{today}.md")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(f"# Trend Digest - {today}\n## Query: {query}\n| Score | Note | Snippet |\n|-------|------|---------|\n")
    for score, rel, snippet in top:
        f.write(f"| {score:.3f} | [[{rel}]] | {snippet} |\n")

print(f"Digest written to {out_file}")
PYEOF
