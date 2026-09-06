#Requires -Version 5.1
<#
.SYNOPSIS
  Interactive installer for the Hermes Brain vault template (native Windows/PowerShell).
#>

$ErrorActionPreference = "Stop"
$TemplateRoot = $PSScriptRoot

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
$Dest = Read-Host "Where should the vault live? [$DefaultDest]"
if ([string]::IsNullOrWhiteSpace($Dest)) { $Dest = $DefaultDest }

$sameLocation = $false
try {
  if ((Resolve-Path $TemplateRoot).Path -eq (Resolve-Path -ErrorAction SilentlyContinue $Dest).Path) {
    $sameLocation = $true
  }
} catch {}

if ($sameLocation) {
  Write-Info "Installing in place at $Dest"
} else {
  if (Test-Path $Dest) {
    $confirm = Read-Host "  $Dest already exists. Overwrite/merge into it? [y/N]"
    if ($confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 1 }
  } else {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
  }
  Write-Info "Copying template to $Dest ..."
  Copy-Item -Path (Join-Path $TemplateRoot "*") -Destination $Dest -Recurse -Force
  Write-Ok "Copied."
}

# ---------------------------------------------------------------------------
# 2. Ask about the trend-digest embedding backend
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "Optional: trend-digest embeddings" -ForegroundColor Cyan
Write-Info "New-TrendDigest.ps1 uses local sentence-transformers (pure Python)."
Write-Info "pipeline.ps1 uses Ollama embeddings instead."
$Backend = Read-Host "Which do you want to set up now? [ollama/python/skip] (skip)"
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
  $setEnv = Read-Host "  Record this vault path in Hermes env as HERMES_VAULT_PATH now? [Y/n]"
  if ($setEnv -notmatch '^[Nn]') {
    try {
      & hermes config set env.HERMES_VAULT_PATH "$Dest"
      Write-Ok "Set env.HERMES_VAULT_PATH"
    } catch {
      Write-Warn "Couldn't set it automatically -- run manually: hermes config set env.HERMES_VAULT_PATH `"$Dest`""
    }
  }
  Write-Info "Next: point your session-archive cron job's output root at this path,"
  Write-Info "and see SETUP.md step 4 for the Daily/ export convention it expects."
} else {
  Write-Warn "Hermes CLI not found on PATH -- skipping auto-config."
  Write-Info "Once installed, run: hermes config set env.HERMES_VAULT_PATH `"$Dest`""
}

# ---------------------------------------------------------------------------
# 5. Optional: run consolidate_memory.py once
# ---------------------------------------------------------------------------
Write-Host ""
$runCons = Read-Host "Run Scripts/consolidate_memory.py once now to verify it works? [y/N]"
if ($runCons -match '^[Yy]') {
  $py = Get-Command python -ErrorAction SilentlyContinue
  if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
  if ($py) {
    & $py.Source (Join-Path $Dest "Scripts\consolidate_memory.py") "$Dest"
  } else {
    Write-Warn "No python/python3 found -- skipping."
  }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
Write-Info "Vault: $Dest"
Write-Info "Read $Dest\SETUP.md and $Dest\Welcome.md for the rest."
