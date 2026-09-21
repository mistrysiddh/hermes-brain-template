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
.PARAMETER DryRun
  Show what would be merged without making any changes.
.PARAMETER Help
  Show usage information.
#>

param(
    [string]$TemplateUrl = "https://github.com/mistrysiddh/hermes-brain-template.git",
    [string]$TemplateBranch = "main",
    [switch]$DryRun,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\update.ps1 [-TemplateUrl <url>] [-TemplateBranch <branch>] [-DryRun] [-Help]"
    Write-Host "  -DryRun        Show what would be merged without making changes"
    Write-Host "  -Help          Show this help"
    exit 0
}

$VaultRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path

$RemoteName = "template"

function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Write-Info($msg) { Write-Host "  $msg" }

Set-Location $VaultRoot

Write-Host ""
Write-Host "Hermes Brain -- template update" -ForegroundColor Cyan
Write-Info "Vault: $VaultRoot"
Write-Info "Template: $TemplateUrl (branch: $TemplateBranch)"
if ($DryRun) { Write-Info "DRY RUN MODE -- no changes will be made" }
Write-Host ""

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { Write-Warn "git not found on PATH -- install Git for Windows first."; exit 1 }

# ---------------------------------------------------------------------------
# 1. First run: turn this vault into a git repo tracking the template.
# ---------------------------------------------------------------------------
if (-not (Test-Path ".git")) {
    Write-Host "No .git found here yet -- setting one up." -ForegroundColor Cyan
    if (-not $DryRun) {
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
        Write-Info "DRY RUN: Would initialize git repository and create baseline commit"
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
        if (-not $DryRun) {
            $doCommit = Read-Host "  Commit them now before updating? [Y/n]"
            if ($doCommit -notmatch '^[Nn]') {
                & git add -A
                & git commit -q -m "Snapshot before template update"
                Write-Ok "Committed."
            } else {
                Write-Warn "Proceeding with uncommitted changes -- they may conflict with the merge."
            }
        } else {
            Write-Info "DRY RUN: Would prompt to commit uncommitted changes"
        }
    }
}

# ---------------------------------------------------------------------------
# 2. Point a dedicated, read-only remote at the template.
# ---------------------------------------------------------------------------
& git remote get-url $RemoteName 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    if (-not $DryRun) {
        & git remote set-url $RemoteName $TemplateUrl
    } else {
        Write-Info "DRY RUN: Would set remote '$RemoteName' to '$TemplateUrl'"
    }
} else {
    if (-not $DryRun) {
        & git remote add $RemoteName $TemplateUrl
    } else {
        Write-Info "DRY RUN: Would add remote '$RemoteName' pointing to '$TemplateUrl'"
    }
}
# Disable push on this remote on purpose: this vault's local git history can
# contain personal-content commits even though the *files* stay gitignored
# (e.g. commit metadata, timing). Never let 'git push template' send that
# anywhere by accident.
if (-not $DryRun) {
    & git remote set-url --push $RemoteName "DISABLED-see-update.ps1"
} else {
    Write-Info "DRY RUN: Would disable push on remote '$RemoteName'"
}

# ---------------------------------------------------------------------------
# 2.5. Protect user-facing scaffold files from future merge conflicts.
#
# Files like User-Profile.md ship in the template as a blank fill-in-the-blank
# note, but the moment you fill it in it becomes personal content -- same
# category as Daily/ or Memory-Review/*. Unlike those folders, this file has
# to be delivered by the template at least once (so new vaults get the blank
# scaffold), which rules out .gitignore -- an ignored path can't be added by
# a future merge either.
#
# Instead, register a local-only "ours" merge driver for these paths (see
# issue #5): on the FIRST pull the file doesn't exist locally yet, so it's
# added cleanly from the template as normal. On every pull AFTER that, if
# you've edited it (you always will, once you fill it in) and the template
# also changes its copy, git resolves the conflict by silently keeping your
# local version instead of stopping with conflict markers. This is local
# vault config only (.git/info/attributes, never synced anywhere) so it
# doesn't touch the template repo itself.
# ---------------------------------------------------------------------------
$PersonalScaffoldFiles = @("User-Profile.md")
if (-not $DryRun) {
    & git config merge.ours.driver true
    New-Item -ItemType Directory -Force -Path ".git/info" | Out-Null
    foreach ($f in $PersonalScaffoldFiles) {
        $attrLine = "$f merge=ours"
        $attrPath = ".git/info/attributes"
        $existing = if (Test-Path $attrPath) { Get-Content $attrPath -Raw } else { "" }
        if ($existing -notmatch [regex]::Escape($attrLine)) {
            Add-Content -Path $attrPath -Value $attrLine
            Write-Info "Protected '$f' from future template merge conflicts (keeps your local edits)."
        }
    }
} else {
    Write-Info "DRY RUN: Would protect personal scaffold files with merge=ours"
}

# ---------------------------------------------------------------------------
# 3. Fetch + merge.
# ---------------------------------------------------------------------------
Write-Host "Fetching template updates..." -ForegroundColor Cyan
if (-not $DryRun) {
    & git fetch $RemoteName $TemplateBranch -q
} else {
    Write-Info "DRY RUN: Would fetch from remote '$RemoteName' branch '$TemplateBranch'"
}

Write-Host "Merging..." -ForegroundColor Cyan
if (-not $DryRun) {
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
        Write-Host ""
        Write-Info "Tip: for files you've customized locally (e.g. .obsidian/themes/*/theme.css,"
        Write-Info ".obsidian/appearance.json), 'git checkout --ours <file>' keeps your version;"
        Write-Info "'git checkout --theirs <file>' takes the template's. See CONTRIBUTING.md."
        exit 1
    }
} else {
    Write-Info "DRY RUN: Would attempt merge from '$RemoteName/$TemplateBranch'"
    Write-Info "DRY RUN: Use 'git fetch $RemoteName $TemplateBranch' and 'git merge-tree' to preview conflicts"
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
if ($DryRun) { Write-Info "This was a dry run -- no changes were made" }
Write-Info "Re-run this script any time to pull future template updates."