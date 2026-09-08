# New-TrendDigest.ps1
# Generates a daily trend digest using local embeddings (sentence-transformers).
# Delegates to Scripts/trend_digest.py — the embedding/ranking logic lives there
# once, shared with trend_digest.sh, instead of being duplicated per shell.
# Output: markdown note in Vault\Research\Trend-Digest\<yyyy-MM-dd>.md
param(
    # Defaults to the vault this script lives in (Scripts\.. = vault root).
    [string]$VaultPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$VenvPython = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"
)
$Query = "local LLM agents offline"
$TopN = 8
$DigestFolder = Join-Path $VaultPath "Research\Trend-Digest"

if (-not (Test-Path $DigestFolder)) {
    New-Item -ItemType Directory -Path $DigestFolder | Out-Null
}

# Prefer a Hermes-managed venv if present, else fall back to python/py on PATH.
$PY = $VenvPython
if (-not (Test-Path $PY)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) { $cmd = Get-Command py -ErrorAction SilentlyContinue }
    if (-not $cmd) {
        Write-Error "No python interpreter found on PATH."
        exit 1
    }
    Write-Warning "Venv python not found at $VenvPython — falling back to '$($cmd.Source)'"
    $PY = $cmd.Source
}

& $PY -c "import sentence_transformers" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "sentence-transformers not installed for $PY.`nInstall it with: $PY -m pip install sentence-transformers numpy"
    exit 1
}

# Pass $VaultPath/$Query as plain strings — PowerShell's call operator already
# keeps a spaced string as one argument, so wrapping it in extra quote characters
# here would inject literal `"` chars into argv and break paths like the
# installer's own default "~\Hermes Brain" (has a space).
$pythonScript = Join-Path $PSScriptRoot "trend_digest.py"
$notesJson = & $PY $pythonScript $VaultPath $Query $TopN
if ($LASTEXITCODE -ne 0) {
    Write-Error "trend_digest.py failed"
    exit 1
}
$notes = $notesJson | ConvertFrom-Json

if (-not $notes) {
    Write-Warning "No notes returned — check that the vault path is correct and contains .md files."
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

Write-Host "`nDigest written to:`n$outFile"
Write-Host "Open it in Obsidian to see click-through links."
