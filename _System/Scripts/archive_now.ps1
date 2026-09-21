# Hermes Brain — instant session archiver (manual trigger) for PowerShell
#
# Exports Hermes chat sessions active since a given time (default: last 5 minutes)
# as redacted markdown, reorganizes them into the vault's Daily/YYYY/MM/DD/ 
# convention, updates manifest.jsonl, and extracts token usage to Token-Usage.log.
#
# Intended to be run manually whenever you want an immediate export (e.g., after
# a long chat session) instead of waiting for the hourly cron.
#
# Only ONE instance (either this script or hourly_archive.ps1) should run against
# a given vault at a time, to avoid manifest.jsonl races.

param(
    [Parameter(Mandatory=$false)]
    [string]$Since = "5m"
)

function Find-Hermes {
    $hermesPath = Get-Command hermes -ErrorAction SilentlyContinue
    if ($hermesPath) { return $hermesPath.Source }
    return "hermes"  # fallback to PATH lookup
}

function Parse-SinceArg {
    param([string]$SinceStr)
    if (-not $SinceStr) { return 300 } # default 5 minutes
    
    $totalSeconds = 0
    $matches = [regex]::Matches($SinceStr.ToLower(), '(\d+)([smhd])')
    foreach ($match in $matches) {
        $value = [int]$match.Groups[1].Value
        $unit = $match.Groups[2].Value
        switch ($unit) {
            's' { $totalSeconds += $value }
            'm' { $totalSeconds += $value * 60 }
            'h' { $totalSeconds += $value * 3600 }
            'd' { $totalSeconds += $value * 86400 }
        }
    }
    if ($totalSeconds -eq 0) {
        try { return [int]$SinceStr * 60 }
        catch { Write-Host "Could not parse '$SinceStr', using default 5m"; return 300 }
    }
    return $totalSeconds
}

function Extract-TokensFromJsonl {
    param([string]$JsonlPath)
    $total = 0
    $sessions = 0
    if (-not (Test-Path $JsonlPath)) { return @($total, $sessions) }
    
    foreach ($line in Get-Content $JsonlPath) {
        $line = $line.Trim()
        if (-not $line) { continue }
        try {
            $rec = $line | ConvertFrom-Json
            $modelConfig = $rec.model_config
            if ($modelConfig) {
                try {
                    $cfg = $modelConfig | ConvertFrom-Json
                    $usage = $cfg._usage_anchor
                    $prompt = [int]($usage.prompt_tokens ?? 0)
                    $completion = [int]($usage.completion_tokens ?? 0)
                    $total += $prompt + $completion
                    $sessions++
                } catch {
                    # Invalid JSON in model_config, skip
                }
            }
        } catch {
            # Invalid JSON line, skip
        }
    }
    return @($total, $sessions)
}

function Update-TokenLog {
    param([int]$DailyTotal, [int]$SessionCount)
    $today = Get-Date -Format "yyyy-MM-dd"
    $line = "{0}: {1} tokens ({2} session(s))`n" -f $today, $DailyTotal, $SessionCount
    $tokenLog = Join-Path $env:HERMES_VAULT_PATH "Skills-Notes\Token-Usage.log"
    $null = New-Item -ItemType Directory -Path (Split-Path $tokenLog) -Force
    Add-Content -Path $tokenLog -Value $line -Encoding UTF8
    
    # Also compute and print running total
    $runningTotal = 0
    if (Test-Path $tokenLog) {
        foreach ($logLine in Get-Content $tokenLog) {
            $logLine = $logLine.Trim()
            if (-not $logLine -or $logLine.StartsWith("#")) { continue }
            $parts = $logLine.Split(":")
            if ($parts.Length -eq 2) {
                $valuePart = $parts[1].Trim().Split(" ")[0]
                if ([int]::TryParse($valuePart, [ref]$num)) { $runningTotal += $num }
            }
        }
    }
    Write-Host "Token usage today: $DailyTotal tokens ($SessionCount session(s))"
    Write-Host "Running total: $runningTotal tokens"
}

function Main {
    # Vault path from environment
    $vaultPath = $env:HERMES_VAULT_PATH
    if (-not $vaultPath) {
        Write-Error "HERMES_VAULT_PATH is not set — aborting."
        exit 1
    }
    
    $dailyCand = Join-Path $vaultPath "04-Archives\Daily"
    $dailyPath = if (Test-Path $dailyCand) { $dailyCand } else { Join-Path $vaultPath "Daily" }
    $manifestPath = Join-Path $dailyPath "manifest.jsonl"
    $lockFile = Join-Path $dailyPath ".hourly_archive.lock"
    
    $tokenCand = Join-Path $vaultPath "04-Archives\Audit-Reports\Token-Usage.log"
    $tokenLogPath = if (Test-Path (Split-Path $tokenCand)) { $tokenCand } else { Join-Path $vaultPath "Skills-Notes\Token-Usage.log" }
    
    # 0. Prevent concurrent execution with hourly_archive.py or another archive_now.ps1
    if (Test-Path $lockFile) {
        Write-Host "Another archive process is already running — exiting."
        exit 0
    }
    
    # Create lock file
    $null = New-Item -ItemType File -Path $lockFile -Force
    
    try {
        $hermesBin = Find-Hermes
        $sinceSeconds = Parse-SinceArg $Since
        $sinceStr = "${sinceSeconds}s"
        
        Write-Host "Exporting sessions from the last $($sinceSeconds/60) minute(s)..."
        
        # 1. Export sessions as markdown (for the vault)
        $cmdMd = @($hermesBin, "sessions", "export", "--format", "md", "--newer-than", $sinceStr, "--redact", "--yes", $dailyPath)
        $resultMd = & $cmdMd 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error $resultMd
            exit $LASTEXITCODE
        }
        Write-Host $resultMd
        
        if ($resultMd -like "*Exported 0 session*") {
            Write-Host "No new sessions in the specified time window."
            return
        }
        
        # 2. ALSO export as JSONL to capture token usage (stdout)
        $cmdJsonl = @($hermesBin, "sessions", "export", "--format", "jsonl", "--newer-than", $sinceStr, "--redact", "--yes", "-")
        $resultJsonl = & $cmdJsonl 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "JSONL export failed: $($resultJsonl)"
            $jsonlPath = $null
        } else {
            # Write JSONL to a temp file for token extraction
            $jsonlPath = Join-Path $dailyPath "tmp_export.jsonl"
            $resultJsonl | Out-File -FilePath $jsonlPath -Encoding UTF8
        }
        
        # 3. Extract token usage from JSONL
        $dailyTotal = 0
        $sessionCount = 0
        if ($jsonlPath -and (Test-Path $jsonlPath)) {
            $tokenResult = Extract-TokensFromJsonl $jsonlPath
            $dailyTotal = $tokenResult[0]
            $sessionCount = $tokenResult[1]
            Update-TokenLog $dailyTotal $sessionCount
            Remove-Item $jsonlPath -Force
        }
        
        # 4. Load existing manifest (dedupe by session_id).
        $existing = @{}
        if (Test-Path $manifestPath) {
            foreach ($line in Get-Content $manifestPath) {
                $line = $line.Trim()
                if (-not $line) { continue }
                try {
                    $rec = $line | ConvertFrom-Json
                    $sid = $rec.session_id
                    if ($sid) { $existing[$sid] = $rec }
                } catch {
                    # Invalid JSON line, skip
                }
            }
        }
        
        # 5. Move flat exported files into YYYY/MM/DD/, updating manifest paths.
        foreach ($fname in Get-ChildItem -Path $dailyPath -Filter *.md | Where-Object { 
                $_.Name -notin @("README.md", "Timeline.md", "Chat-Correlation.md", "tmp_export.jsonl")
            }) {
            $fpath = $fname.FullName
            $head = Get-Content -Path $fpath -TotalCount 2000 -Raw
            
            # Extract date from created_at
            if ($head -match 'created_at:\s*"(\d{4})-(\d{2})-(\d{2})"') {
                $y = $matches[1].Value
                $mo = $matches[2].Value
                $d = $matches[3].Value
                
                # Extract session_id
                $sessionId = $null
                if ($head -match 'session_id:\s*"([^"]+)"') {
                    $sessionId = $matches[1].Value
                }
                
                $destDir = Join-Path $dailyPath Join-Path $y (Join-Path $mo $d)
                $null = New-Item -ItemType Directory -Path $destDir -Force
                $destPath = Join-Path $destDir $fname.Name
                
                if (Test-Path $destPath) {
                    Remove-Item $fpath -Force  # duplicate re-export of same session, drop
                } else {
                    Move-Item -Path $fpath -Destination $destPath
                }
                
                if ($sessionId) {
                    $title = $null
                    $msgCount = $null
                    if ($head -match 'title:\s*"([^"]*)"') { $title = $matches[1].Value }
                    if ($head -match 'message_count:\s*(\d+)') { $msgCount = [int]$matches[1].Value }
                    
                    $existing[$sessionId] = @{
                        session_id = $sessionId
                        title = $title
                        path = $destPath
                        format = "md"
                        message_count = $msgCount
                        exported_at = (Get-Item $destPath).LastWriteTimeUtc.ToFileTimeUtc()
                    }
                }
            }
        }
        
        # 6. Rewrite manifest, sorted by exported_at.
        $records = $existing.Values | Sort-Object { $_.exported_at }
        $null = $manifestPath | Set-Content -Value ($records | ForEach-Object { $_ | ConvertTo-Json -Compress }) -Encoding UTF8
        
        Write-Host ("Manifest now has {0} session(s) indexed." -f $records.Count)
    } finally {
        # Release lock
        if (Test-Path $lockFile) { Remove-Item $lockFile -Force }
    }
}

Main