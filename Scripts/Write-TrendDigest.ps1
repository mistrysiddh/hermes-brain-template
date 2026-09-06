# Write-TrendDigest.ps1
# Uses the Python script to generate digest and write to file
# Defaults assume this script lives in <vault>\Scripts\ — override with params if needed.
param(
    [string]$VaultPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$VenvPython = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"
)
$Query = "local LLM agents offline"
$TopN = 8
$DigestFolder = Join-Path $VaultPath "Research\Trend-Digest"

if (-not (Test-Path $DigestFolder)) {
    New-Item -ItemType Directory -Path $DigestFolder | Out-Null
}

# Path to venv python (falls back to system python if the Hermes venv isn't found)
$venvPython = $VenvPython
if (-not (Test-Path $venvPython)) {
    Write-Warning "Venv python not found at $venvPython — falling back to 'python' on PATH"
    $venvPython = "python"
}

# Run the Python script and capture JSON
$pythonScript = Join-Path $PSScriptRoot "trend_digest.py"
$notesJson = & $venvPython $pythonScript "`"$VaultPath`"" "`"$Query`"" $TopN
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python script failed"
    exit 1
}
$notes = $notesJson | ConvertFrom-Json

if (-not $notes) {
    Write-Warning "No notes returned"
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