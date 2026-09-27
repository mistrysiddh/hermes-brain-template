# uninstall.ps1 — cleanly remove a Hermes Brain vault installation.
# Mirrors install.ps1's setup steps in reverse.
$ErrorActionPreference = "Stop"

function Write-Bold($msg) { Write-Host $msg -ForegroundColor White }
function Write-Info($msg) { Write-Host "  $msg" }
function Write-Warn($msg) { Write-Host "  ! $msg" -ForegroundColor Yellow }
function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }

Write-Host ""
Write-Bold "Hermes Brain -- vault uninstaller"
Write-Info "Reverses what install.ps1 set up: Hermes CLI wiring, then (optionally)"
Write-Info "the vault directory itself. Nothing is deleted without confirmation."
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Ask which vault to uninstall
# ---------------------------------------------------------------------------
$DefaultDest = Join-Path $HOME "Hermes Brain"
$Dest = Read-Host "Vault path to uninstall [$DefaultDest]"
if ([string]::IsNullOrWhiteSpace($Dest)) { $Dest = $DefaultDest }

if (-not (Test-Path $Dest)) {
  Write-Warn "$Dest doesn't exist -- nothing to remove there."
}

# ---------------------------------------------------------------------------
# 2. Unset HERMES_VAULT_PATH if it points at this vault
# ---------------------------------------------------------------------------
Write-Host ""
Write-Bold "Hermes CLI wiring"
$hermesCmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermesCmd) {
  Write-Ok "Hermes CLI found."
  $current = $null
  try { $current = (hermes config get env.HERMES_VAULT_PATH 2>$null) } catch {}
  if ($current -and ($current.Trim() -eq $Dest)) {
    $unset = Read-Host "  Unset env.HERMES_VAULT_PATH (currently set to this vault)? [Y/n]"
    if ($unset.ToLower() -ne "n") {
      try {
        hermes config unset env.HERMES_VAULT_PATH
        Write-Ok "Unset env.HERMES_VAULT_PATH"
      } catch {
        Write-Warn "Couldn't unset automatically -- run manually: hermes config unset env.HERMES_VAULT_PATH"
      }
    }
  } elseif ($current) {
    Write-Info "env.HERMES_VAULT_PATH is set to a different vault ($current) -- leaving it alone."
  } else {
    Write-Info "env.HERMES_VAULT_PATH isn't set -- nothing to unset."
  }
} else {
  Write-Warn "Hermes CLI not found on PATH -- skipping."
}

# ---------------------------------------------------------------------------
# 3. Cron job & hooks cleanup
# ---------------------------------------------------------------------------
Write-Host ""
Write-Bold "Cron job & hooks cleanup"
if ($hermesCmd) {
  $cronJobs = & hermes cron list 2>&1
  if ($cronJobs -match "hermes-brain-archive-hourly") {
    $rmCron = Read-Host "  Found 'hermes-brain-archive-hourly' cron job. Remove it now? [Y/n]"
    if ($rmCron -notmatch '^[Nn]') {
      try {
        & hermes cron delete hermes-brain-archive-hourly
        Write-Ok "Removed 'hermes-brain-archive-hourly' cron job."
      } catch {
        Write-Warn "Could not remove cron job automatically -- run: hermes cron delete hermes-brain-archive-hourly"
      }
    }
  } else {
    Write-Info "No 'hermes-brain-archive-hourly' cron job found."
  }
} else {
  Write-Info "Hermes CLI not found -- if you had an hourly cron job set up, remove it via Hermes chat or CLI."
}

# Clean up hooks from config.yaml if they reference this vault
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if ($py) {
  $pyHookCleanup = @"
import os, sys
try:
    import yaml
except ImportError:
    yaml = None

hermes_cfg = os.path.expandvars(r'%LOCALAPPDATA%\hermes\config.yaml')
if not os.path.exists(hermes_cfg):
    hermes_cfg = os.path.expanduser('~/.hermes/config.yaml')

if os.path.exists(hermes_cfg) and yaml:
    try:
        with open(hermes_cfg, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        hooks = cfg.get('hooks', {})
        dest_norm = os.path.normpath(r'$Dest').lower()
        modified = False
        for evt in list(hooks.keys()):
            if isinstance(hooks[evt], list):
                new_list = [e for e in hooks[evt] if not (isinstance(e, dict) and dest_norm in os.path.normpath(e.get('command', '')).lower())]
                if len(new_list) != len(hooks[evt]):
                    hooks[evt] = new_list
                    modified = True
        if modified:
            with open(hermes_cfg, 'w', encoding='utf-8') as f:
                yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False)
            print('HOOKS_REMOVED')
    except Exception:
        pass
"@
  $hRes = & $py.Source -c $pyHookCleanup 2>&1
  if ($hRes -match "HOOKS_REMOVED") {
    Write-Ok "Removed vault hooks from Hermes config.yaml."
  }
}

# ---------------------------------------------------------------------------
# 4. Optionally delete the vault directory
# ---------------------------------------------------------------------------
Write-Host ""
Write-Bold "Vault directory"
if (Test-Path $Dest) {
  Write-Warn "This will permanently delete: $Dest"
  Write-Warn "That includes any real chat archives, Memory-Review candidates, and"
  Write-Warn "Research notes you've accumulated -- this is NOT recoverable."
  $confirm = Read-Host "  Type the vault path again to confirm deletion, or press Enter to keep it"
  if ($confirm -eq $Dest) {
    Remove-Item -Recurse -Force $Dest
    Write-Ok "Deleted $Dest"
  } else {
    Write-Info "Skipped -- vault directory left in place at $Dest"
  }
} else {
  Write-Info "Nothing to delete -- $Dest doesn't exist."
}

Write-Host ""
Write-Bold "Done."
Write-Info "If you had this vault open in Obsidian, close that window/vault manually."
