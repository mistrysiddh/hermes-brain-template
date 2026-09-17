# Hermes Brain — session enrichment (optional) for PowerShell
#
# Adds a simple summary frontmatter to archived session markdown files
# that don't already have one. The summary is a heuristic: first non-empty
# line of content (or first 200 characters) truncated to one line.
#
# Intended to be run manually or via cron after archiving, to make sessions
# more glanceable and to provide seed data for future memory pipeline steps.
#
# Only standard library is used — no external dependencies.

param(
    [Parameter(Mandatory=$false)]
    [string]$Path = (Join-Path $env:HERMES_VAULT_PATH "Daily"),
    
    [Parameter(Mandatory=$false)]
    [string]$Extension = ".md"
)

function Has-Frontmatter {
    param([string]$Content)
    return $Content -like '---`n*'
}

function Extract-FrontmatterAndBody {
    param([string]$Content)
    if (-not (Has-Frontmatter $Content)) {
        return @(@{}, $Content)
    }
    
    $lines = $Content -split "`n"
    if ($lines.Length -lt 3 -or $lines[0].Trim() -ne '---') {
        return @(@{}, $Content)
    }
    
    $fmLines = @()
    $i = 1
    while ($i -lt $lines.Length) {
        if ($lines[$i].Trim() -eq '---') {
            $i++
            break
        }
        $fmLines += $lines[$i]
        $i++
    }
    
    $frontmatter = $fmLines -join "`n"
    $body = $lines[$i..($lines.Length-1)] -join "`n"
    
    # Parse simple key:value frontmatter (we only care about summary)
    $fmDict = @{}
    foreach ($line in $frontmatter -split "`n") {
        if ($line -match '^\s*([^:]+?)\s*:\s*(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $fmDict[$key] = $value
        }
    }
    
    return @($fmDict, $body)
}

function Set-Frontmatter {
    param([hashtable]$FmDict, [string]$Body)
    $lines = @('---')
    foreach ($key in $FmDict.Keys) {
        $lines += "$key`: $($FmDict[$key])"
    }
    $lines += '---'
    $lines += $Body
    return $lines -join "`n"
}

function Generate-Summary {
    param([string]$Body)
    foreach ($line in $Body -split "`n") {
        if ($line.Trim()) {
            $summary = $line.Trim()
            if ($summary.Length -gt 200) {
                $summary = $summary.Substring(0, 200) + '...'
            }
            return $summary
        }
    }
    return "(no content)"
}

function Process-File {
    param([string]$FilePath)
    try {
        $content = Get-Content -Path $FilePath -Raw -Encoding UTF8
    } catch {
        Write-Host "  Failed to read $FilePath: $_"
        return $false
    }
    
    $fmDictBody = Extract-FrontmatterAndBody $content
    $fmDict = $fmDictBody[0]
    $body = $fmDictBody[1]
    
    if ($fmDict.ContainsKey("summary")) {
        # Already has a summary, skip
        return $false
    }
    
    $summary = Generate-Summary $body
    $fmDict["summary"] = $summary
    $newContent = Set-Frontmatter $fmDict $body
    
    if ($newContent -eq $content) {
        # No change
        return $false
    }
    
    try {
        Set-Content -Path $FilePath -Value $newContent -Encoding UTF8
        Write-Host "  Enriched $FilePath"
        return $true
    } catch {
        Write-Host "  Failed to write $FilePath: $_"
        return $false
    }
}

function Main {
    # Vault path from environment
    $vaultPath = $env:HERMES_VAULT_PATH
    if (-not $vaultPath) {
        Write-Error "HERMES_VAULT_PATH is not set — aborting."
        exit 1
    }
    
    $searchPath = $Path
    if (-not (Test-Path $searchPath -PathType Container)) {
        Write-Error "Search path '$searchPath' does not exist or is not a directory."
        exit 1
    }
    
    $enrichedCount = 0
    $totalCount = 0
    
    Get-ChildItem -Path $searchPath -Recurse -Filter "*$Extension" | ForEach-Object {
        $totalCount++
        if (Process-File $_.FullName) {
            $enrichedCount++
        }
    }
    
    Write-Host ""
    Write-Host "Processed $totalCount $Extension files, enriched $enrichedCount."
}

Main