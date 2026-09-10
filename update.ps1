#Requires -Version 5.1
<#
.SYNOPSIS
  Pull template updates into an already-installed Hermes Brain vault (native Windows/PowerShell).
.DESCRIPTION
  install.sh/.ps1 do a one-shot copy with no .git in the destination, so there
  was previously no safe way to pull in template changes (a new Dashboard
  note, an updated bundled plugin, a fixed script) without blindly
  overwriting hand-edited files. This turns the vault into a local git repo
  tracking the template as a read-only remote, then fetches + merges --
  git's own 3-way merge surfaces conflicts on anything you edited yourself
  instead of silently clobbering it.

  Your personal content (Daily/, Memory-Review/*, Projects/* beyond README,
  plugin data.json, etc.) is protected the same way it always was: this
  vault's own .gitignore already excludes it, so it's never part of the
  diff/merge in the first place.
.PARAMETER TemplateUrl
  Git URL of the template repo. Defaults to the upstream Hermes Brain template.
.PARAMETER TemplateBranch
  Branch to pull from. Defaults to "main".
#>
param(
  [string]$TemplateUrl = "https://github.com/mistrysiddh/hermes-brain-template.git",
  [string]$TemplateBranch = "main"
)

$ErrorActionPreference = "Stop"
$VaultRoot = $PSScriptRoot
$RemoteName = "template"

function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Write-Info($msg) { Write-Host "  $msg" }

Set-Location $VaultRoot

Write-Host ""
Write-Host "Hermes Brain -- template update" -ForegroundColor Cyan
Write-Info "Vault: $VaultRoot"
Write-Info "Template: $TemplateUrl (branch: $TemplateBranch)"
Write-Host ""

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { Write-Warn "git not found on PATH -- install Git for Windows first."; exit 1 }

# ---------------------------------------------------------------------------
# 1. First run: turn this vault into a git repo tracking the template.
# ---------------------------------------------------------------------------
if (-not (Test-Path ".git")) {
  Write-Host "No .git found here yet -- setting one up." -ForegroundColor Cyan
  & git init -q
  & git checkout -b $TemplateBranch -q 2>$null
  if ($LASTEXITCODE -ne 0) { & git branch -m $TemplateBranch }

  # Baseline commit so the merge below has something to diff against.
  # Respects the vault's existing .gitignore, so personal content never
  # enters this local history.
  & git add -A
  & git diff --cached --quiet
  if ($LASTEXITCODE -ne 0) {
    & git commit -q -m "Snapshot before first template update"
    Write-Ok "Committed a local snapshot of your current vault state."
  } else {
    Write-Info "Nothing to snapshot (empty vault)."
  }
} else {
  # Already a repo (either a prior run of this script, or the user cloned
  # the template directly instead of using install.ps1 -- in that case just
  # use plain git pull, don't set up a redundant remote pointing at itself).
  $existingUrl = & git remote get-url origin 2>$null
  if ($existingUrl -eq $TemplateUrl) {
    Write-Warn "This vault's 'origin' already IS the template repo -- just run 'git pull' directly."
    exit 0
  }

  $status = & git status --porcelain
  if ($status) {
    Write-Warn "You have uncommitted changes."
    $doCommit = Read-Host "  Commit them now before updating? [Y/n]"
    if ($doCommit -notmatch '^[Nn]') {
      & git add -A
      & git commit -q -m "Snapshot before template update"
      Write-Ok "Committed."
    } else {
      Write-Warn "Proceeding with uncommitted changes -- they may conflict with the merge."
    }
  }
}

# ---------------------------------------------------------------------------
# 2. Point a dedicated, read-only remote at the template.
# ---------------------------------------------------------------------------
& git remote get-url $RemoteName 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
  & git remote set-url $RemoteName $TemplateUrl
} else {
  & git remote add $RemoteName $TemplateUrl
}
# Disable push on this remote on purpose: this vault's local git history can
# contain personal-content commits even though the *files* stay gitignored
# (e.g. commit metadata, timing). Never let 'git push template' send that
# anywhere by accident.
& git remote set-url --push $RemoteName "DISABLED-see-update.ps1"

# ---------------------------------------------------------------------------
# 3. Fetch + merge.
# ---------------------------------------------------------------------------
Write-Host "Fetching template updates..." -ForegroundColor Cyan
& git fetch $RemoteName $TemplateBranch -q

Write-Host "Merging..." -ForegroundColor Cyan
& git merge "$RemoteName/$TemplateBranch" --allow-unrelated-histories -m "Merge template update ($TemplateBranch)"
if ($LASTEXITCODE -eq 0) {
  Write-Ok "Updated cleanly -- no conflicts."
} else {
  Write-Host ""
  Write-Warn "Merge produced conflicts. Resolve them, then:"
  Write-Info "  git add <resolved files>"
  Write-Info "  git commit"
  Write-Host ""
  Write-Info "Conflicting files:"
  & git diff --name-only --diff-filter=U | ForEach-Object { Write-Info "    $_" }
  exit 1
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
Write-Info "Re-run this script any time to pull future template updates."
