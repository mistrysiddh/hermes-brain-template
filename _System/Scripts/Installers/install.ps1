#Requires -Version 5.1
<#
.SYNOPSIS
  Interactive installer for the Hermes Brain vault template (native Windows/PowerShell).
.PARAMETER Test
  Run self-test after installation (validates scripts, manifest, dashboard).
.PARAMETER Help
  Show usage information.
#>

param(
    [string]$Dest = "",
    [string]$Backend = "",
    [switch]$Test,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\install.ps1 [-Dest <path>] [-Backend <ollama|python|skip>] [-Test] [-Help]"
    Write-Host "  -Dest     Destination path for the vault (default: ~/Hermes Brain)"
    Write-Host "  -Backend  Trend-digest embedding backend: ollama, python, or skip"
    Write-Host "  -Test     Run self-test after installation (validates scripts, manifest, dashboard)"
    Write-Host "  -Help     Show this help"
    exit 0
}

$RepoUrl = "https://github.com/mistrysiddh/hermes-brain-template.git"
$ZipUrl = "https://github.com/mistrysiddh/hermes-brain-template/archive/refs/heads/main.zip"

$TemplateRoot = ""
if ($PSScriptRoot) {
    $candidate = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..") -ErrorAction SilentlyContinue).Path
    if ($candidate -and (Test-Path (Join-Path $candidate "_System"))) {
        $TemplateRoot = $candidate
    }
}
$isRemote = [string]::IsNullOrEmpty($TemplateRoot)

function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Write-Info($msg) { Write-Host "  $msg" }

Write-Host ""
Write-Host "Hermes Brain -- vault installer" -ForegroundColor Cyan
Write-Info "Sets up a personal Obsidian memory vault for a Hermes agent."
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Ask where the vault should live
# ---------------------------------------------------------------------------
$DefaultDest = Join-Path $HOME "Hermes Brain"
if ([string]::IsNullOrWhiteSpace($Dest)) {
    $Dest = Read-Host "Where should the vault live? [$DefaultDest]"
}
if ([string]::IsNullOrWhiteSpace($Dest)) { $Dest = $DefaultDest }


if ($isRemote) {
  if (Test-Path $Dest) {
    $confirm = Read-Host "  $Dest already exists. Overwrite/merge into it? [y/N]"
    if ($confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 1 }
  } else {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
  }

  $git = Get-Command git -ErrorAction SilentlyContinue
  if ($git) {
    Write-Info "Cloning template from GitHub ($RepoUrl) ..."
    & git clone $RepoUrl "$Dest"
    if ($LASTEXITCODE -eq 0) {
      Write-Ok "Cloned template successfully."
    } else {
      Write-Warn "git clone failed -- attempting direct zip download fallback."
      $git = $null
    }
  }

  if (-not $git) {
    Write-Info "Downloading template archive from GitHub ..."
    $tempZip = Join-Path ([System.IO.Path]::GetTempPath()) ("hermes-brain-template-" + [System.Guid]::NewGuid().ToString() + ".zip")
    $tempExtract = Join-Path ([System.IO.Path]::GetTempPath()) ("hermes-brain-extract-" + [System.Guid]::NewGuid().ToString())
    Invoke-RestMethod -Uri $ZipUrl -OutFile $tempZip
    Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
    $extractedFolder = Join-Path $tempExtract "hermes-brain-template-main"
    Copy-Item -Path (Join-Path $extractedFolder "*") -Destination $Dest -Recurse -Force
    Remove-Item $tempZip, $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
    Write-Ok "Downloaded and extracted template."
  }
} else {
  $sameLocation = $false
  try {
    if ((Resolve-Path $TemplateRoot).Path -eq (Resolve-Path -ErrorAction SilentlyContinue $Dest).Path) {
      $sameLocation = $true
    }
  } catch {}

  if ($sameLocation) {
    Write-Info "Configuring in place at $Dest"
  } else {
    if (Test-Path $Dest) {
      $confirm = Read-Host "  $Dest already exists. Overwrite/merge into it? [y/N]"
      if ($confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 1 }
    } else {
      New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    }
    Write-Info "Copying template to $Dest ..."
    Get-ChildItem -Path $TemplateRoot -Force | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
      Copy-Item -Path $_.FullName -Destination $Dest -Recurse -Force
    }
    Write-Ok "Copied."
  }
}


# ---------------------------------------------------------------------------
# 2. Ask about the trend-digest embedding backend
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "Optional: trend-digest embeddings" -ForegroundColor Cyan
Write-Info "New-TrendDigest.ps1 uses local sentence-transformers (pure Python)."
if ([string]::IsNullOrWhiteSpace($Backend)) {
  $Backend = Read-Host "Which do you want to set up now? [ollama/python/skip] (skip)"
}
if ([string]::IsNullOrWhiteSpace($Backend)) { $Backend = "skip" }


switch ($Backend.ToLower()) {
  "ollama" {
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollama) {
      Write-Ok "Ollama found."
      $models = & ollama list 2>$null
      if ($models -notmatch "nomic-embed-text") {
        $pull = Read-Host "  Pull the nomic-embed-text model now? [Y/n]"
        if ($pull -notmatch '^[Nn]') {
          try { & ollama pull nomic-embed-text } catch { Write-Warn "Pull failed -- run 'ollama pull nomic-embed-text' manually later." }
        }
      }
    } else {
      Write-Warn "Ollama not found. Install it from https://ollama.com then run: ollama pull nomic-embed-text"
    }
  }
  "python" {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $py) {
      Write-Warn "No python/python3 found on PATH -- install Python 3 first."
    } else {
      $check = & $py.Source -c "import sentence_transformers" 2>$null
      if ($LASTEXITCODE -eq 0) {
        Write-Ok "sentence-transformers already installed."
      } else {
        $installIt = Read-Host "  Install sentence-transformers + numpy now via pip? [Y/n]"
        if ($installIt -notmatch '^[Nn]') {
          & $py.Source -m pip install --quiet sentence-transformers numpy
          if ($LASTEXITCODE -eq 0) { Write-Ok "Installed." } else { Write-Warn "pip install failed -- try manually." }
        }
      }
    }
  }
  default { Write-Info "Skipping -- run either script manually later." }
}

# ---------------------------------------------------------------------------
# 3. Obsidian check
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "Obsidian" -ForegroundColor Cyan
$obsidianFound = $false
$obsidianPaths = @(
  "$env:LOCALAPPDATA\Obsidian\Obsidian.exe",
  "$env:PROGRAMFILES\Obsidian\Obsidian.exe"
)
foreach ($p in $obsidianPaths) { if (Test-Path $p) { $obsidianFound = $true } }
if ($obsidianFound) {
  Write-Ok "Obsidian appears to be installed."
} else {
  Write-Warn "Couldn't confirm Obsidian is installed -- get it from https://obsidian.md"
}
Write-Info "Open `"$Dest`" as a vault in Obsidian, then enable: Dataview, Smart Connections,"
Write-Info "Local REST API (and brain-atlas if present) under Settings -> Community Plugins."

# ---------------------------------------------------------------------------
# 4. Hermes CLI wiring
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "Hermes integration" -ForegroundColor Cyan
$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermes) {
  Write-Ok "Hermes CLI found."
  if (-not $Test) {
    $setEnv = Read-Host "  Record this vault path in Hermes env as HERMES_VAULT_PATH now? [Y/n]"
    if ($setEnv -notmatch '^[Nn]') {
      try {
        & hermes config set env.HERMES_VAULT_PATH "$Dest"
        Write-Ok "Set env.HERMES_VAULT_PATH"
      } catch {
        Write-Warn "Couldn't set it automatically -- run manually: hermes config set env.HERMES_VAULT_PATH `"$Dest`""
      }
    }
    Write-Host ""
    Write-Host "Hourly session-archiving cron job" -ForegroundColor Cyan
    $setupCron = Read-Host "  Set up hourly session archiving cron job in Hermes now? [Y/n]"
    if ($setupCron -notmatch '^[Nn]') {
      $existingJobs = & hermes cron list 2>&1
      if ($existingJobs -match "hermes-brain-archive-hourly") {
        Write-Ok "Cron job 'hermes-brain-archive-hourly' is already registered."
      } else {
        $archivePrompt = "Run the Hermes Brain hourly session archiver. Execute: python `"$Dest\_System\Scripts\hourly_archive.py`". This exports Hermes chat sessions from the last hour as redacted markdown into the vault's 04-Archives/Daily/YYYY/MM/DD/ folder structure, updates 04-Archives/Daily/manifest.jsonl, extracts token usage, and appends to 04-Archives/Audit-Reports/Token-Usage.log. Report the output briefly."
        & hermes cron create "0 * * * *" "$archivePrompt" --name "hermes-brain-archive-hourly"
        if ($LASTEXITCODE -eq 0) {
          Write-Ok "Created hourly archiving cron job 'hermes-brain-archive-hourly'."
        } else {
          Write-Warn "Could not create cron job automatically -- see INSTALL_PROMPT.md."
        }
      }
    }
  } else {
    Write-Info "Test mode: skipping Hermes env and cron configuration prompts."
  }
} else {
  Write-Warn "Hermes CLI not found on PATH -- skipping auto-config."
  Write-Info "Once installed, run: hermes config set env.HERMES_VAULT_PATH `"$Dest`""
}

# ---------------------------------------------------------------------------
# 5. Optional: run consolidate_memory.py once
# ---------------------------------------------------------------------------
if (-not $Test) {
  Write-Host ""
  $runCons = Read-Host "Run _System/Scripts/consolidate_memory.py once now to verify it works? [y/N]"
  if ($runCons -match '^[Yy]') {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
    if ($py) {
      $consPath = if (Test-Path (Join-Path $Dest "_System\Scripts\consolidate_memory.py")) {
        Join-Path $Dest "_System\Scripts\consolidate_memory.py"
      } else {
        Join-Path $Dest "Scripts\consolidate_memory.py"
      }
      & $py.Source $consPath "$Dest"
    } else {
      Write-Warn "No python/python3 found -- skipping."
    }
  }
}

# ---------------------------------------------------------------------------
# 6. Self-test (if -Test flag provided)
# ---------------------------------------------------------------------------
if ($Test) {
  Write-Host ""
  Write-Host "Running self-test..." -ForegroundColor Cyan
  
  $py = Get-Command python -ErrorAction SilentlyContinue
  if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
  
  if ($py) {
    Write-Info "Test 1: Python script syntax validation..."
    $scriptsDir = Join-Path $Dest "_System\Scripts"
    if (-not (Test-Path $scriptsDir)) { $scriptsDir = Join-Path $Dest "Scripts" }
    $compileCode = "import py_compile, sys; [py_compile.compile(f) for f in sys.argv[1:]]"
    & $py.Source -c $compileCode (Join-Path $scriptsDir "hourly_archive.py") (Join-Path $scriptsDir "consolidate_memory.py") (Join-Path $scriptsDir "skill_forecast.py") (Join-Path $scriptsDir "session_tagger.py") 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Ok "All Python scripts compile cleanly" } else { Write-Warn "Some Python scripts have syntax errors" }
    
    # Test 2: Validate manifest.jsonl structure (if exists)
    Write-Info "Test 2: Manifest structure validation..."
    $manifestCand = Join-Path $Dest "04-Archives\Daily\manifest.jsonl"
    $manifestPath = if (Test-Path $manifestCand) { $manifestCand } else { Join-Path $Dest "Daily\manifest.jsonl" }

    if (Test-Path $manifestPath) {
      if ((Get-Item $manifestPath).Length -eq 0) {
        Write-Ok "Manifest.jsonl exists (empty, ready for session archives)"
      } else {
        $pythonCode = @"
import json, sys
errors = 0
with open(r'$manifestPath') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if 'session_id' not in rec:
                print(f'Line {i}: missing session_id')
                errors += 1
            if 'path' not in rec:
                print(f'Line {i}: missing path')
                errors += 1
        except json.JSONDecodeError as e:
            print(f'Line {i}: JSON decode error: {e}')
            errors += 1
if errors == 0:
    print('Manifest structure OK')
else:
    print(f'Manifest has {errors} errors')
    sys.exit(1)
"@
        $result = & $py.Source -c $pythonCode 2>$null
        if ($LASTEXITCODE -eq 0) { Write-Ok "Manifest.jsonl structure valid" } else { Write-Warn "Manifest.jsonl has issues" }
      }
    } else {
      New-Item -ItemType File -Path $manifestPath -Force | Out-Null
      Write-Ok "Manifest file created (empty)"
    }
    
    Write-Info "Test 3: Dashboard file validation..."
    if (Test-Path (Join-Path $Dest "Dashboard.md") -PathType Leaf) { Write-Ok "Dashboard.md exists" } else { Write-Warn "Dashboard.md not found" }
    
    Write-Info "Test 4: Required directories..."
    foreach ($dir in "01-Projects", "02-Areas", "03-Resources", "04-Archives", "_System", "assets") {
      if (Test-Path (Join-Path $Dest $dir) -PathType Container) { Write-Ok "  $dir/" } else { Write-Warn "  $dir/ missing" }
    }
    
    Write-Info "Test 5: Key files..."
    foreach ($file in "Welcome.md", "MOC.md", "README.md", "SETUP.md", "Dashboard.md", "INSTALL_PROMPT.md") {
      if (Test-Path (Join-Path $Dest $file) -PathType Leaf) { Write-Ok "  $file" } else { Write-Warn "  $file missing" }
    }
    
    Write-Host ""
    Write-Host "Self-test complete." -ForegroundColor Cyan
  } else {
    Write-Warn "No Python found -- limited self-test only"
    if (Test-Path (Join-Path $Dest "Dashboard.md") -PathType Leaf) { Write-Ok "Dashboard.md exists" } else { Write-Warn "Dashboard.md missing" }
    foreach ($dir in "01-Projects", "02-Areas", "03-Resources", "04-Archives", "_System") {
      if (Test-Path (Join-Path $Dest $dir) -PathType Container) { Write-Ok "  $dir/" } else { Write-Warn "  $dir/ missing" }
    }
  }
}


Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
Write-Info "Vault: $Dest"
Write-Info "Read $Dest\SETUP.md and $Dest\Welcome.md for the rest."
