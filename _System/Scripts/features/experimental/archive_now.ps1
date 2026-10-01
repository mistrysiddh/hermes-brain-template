# Hermes Brain — instant session archiver (manual trigger) for PowerShell
#
# Delegates directly to archive_now.py to ensure database-aware session discovery,
# robust locking, and clean slug management.

param(
    [Parameter(Mandatory=$false)]
    [string]$Since = "5m",
    [Parameter(Mandatory=$false)]
    [string]$SessionId = "",
    [Parameter(Mandatory=$false)]
    [string]$Vault = "",
    [switch]$Enrich
)

$scriptPy = Join-Path $PSScriptRoot "archive_now.py"
$pyArgs = @()

if ($SessionId) {
    $pyArgs += @("--session-id", $SessionId)
} else {
    if ($Since) { $pyArgs += @("--since", $Since) }
}

if ($Vault) {
    $pyArgs += @("--vault", $Vault)
}

if ($Enrich) {
    $pyArgs += @("--enrich")
}

& python $scriptPy @pyArgs
exit $LASTEXITCODE