# New-TrendDigest.ps1
# Generates a daily trend digest using local embeddings (sentence-transformers)
# Output: markdown note in Vault\Research\Trend-Digest\<yyyy-MM-dd>.md

# -------------------------- USER SETTINGS --------------------------
# Defaults to the vault this script lives in (Scripts\.. = vault root).
# Override with -VaultPath if you keep the vault somewhere else.
param(
    [string]$VaultPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)
$Query = "local LLM agents offline"
$TopN = 8
$DigestFolder = Join-Path $VaultPath "Research\Trend-Digest"
# -------------------------------------------------------------------

# Ensure output folder exists
if (-not (Test-Path $DigestFolder)) {
    New-Item -ItemType Directory -Path $DigestFolder | Out-Null
}

# Define Python script as a string
$pythonScript = @"
import os, sys, json, numpy as np
from sentence_transformers import SentenceTransformer

def main():
    vault = sys.argv[1]
    query = sys.argv[2]
    top_n = int(sys.argv[3])

    docs = []
    paths = []
    for root, _, files in os.walk(vault):
        for f in files:
            if f.lower().endswith('.md'):
                full = os.path.join(root, f)
                try:
                    with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
                        text = fh.read()
                        # Strip simple YAML frontmatter
                        if text.startswith('---'):
                            parts = text.split('---', 2)
                            if len(parts) >= 3:
                                text = parts[2]
                        text = text.strip()
                        if not text:
                            continue
                        docs.append(text[:800])  # truncate to keep memory sane
                        paths.append(full)
                except Exception as e:
                    # skip unreadable files
                    pass

    if not docs:
        print(json.dumps([]))
        return

    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)

    doc_emb = model.encode(docs, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
    doc_emb_norm = doc_emb / np.linalg.norm(doc_emb, axis=1, keepdims=True)

    q_emb = model.encode([query], convert_to_numpy=True)[0]
    q_emb_norm = q_emb / np.linalg.norm(q_emb)

    sims = np.dot(doc_emb_norm, q_emb_norm)
    top_idx = np.argsort(sims)[::-1][:top_n]

    results = []
    for idx in top_idx:
        score = float(sims[idx])
        rel_path = os.path.relpath(paths[idx], vault)
        snippet = docs[idx].replace('\n', ' ')[:220]
        results.append({
            "path": rel_path.replace('\\', '/'),
            "score": round(score, 4),
            "snippet": snippet
        })

    print(json.dumps(results, ensure_ascii=False))

if __name__ == '__main__':
    main()
"@

# Write Python script to a temporary file
$tempPy = Join-Path $env:TEMP "embed_script.py"
$pythonScript | Out-File -FilePath $tempPy -Encoding UTF8

# Run Python script and capture JSON output
$notesJson = & python $tempPy "`"$VaultPath`"" "`"$Query`"" $TopN
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python script failed"
    exit 1
}
$notes = $notesJson | ConvertFrom-Json

if (-not $notes) {
    Write-Warning "No notes returned – check that the vault path is correct and contains .md files."
    exit 1
}

# Build digest markdown
$today = Get-Date -Format "yyyy-MM-dd"
$outFile = Join-Path $DigestFolder "$today.md"

$header = "# Trend Digest - $today`n## Query: $Query`n| Score | Note | Snippet |`n|-------|------|---------|"
$header | Out-File -FilePath $outFile -Encoding UTF8

foreach ($n in $notes) {
    $line = "| {0:F4} | [[{1}]] | {2} |" -f $n.score, ($n.path -replace '\\','/'), $n.snippet
    $line | Out-File -FilePath $outFile -Append -Encoding UTF8
}

Write-Host "`n✅ Digest written to:`n$outFile"
Write-Host "Open it in Obsidian to see click‑through links."