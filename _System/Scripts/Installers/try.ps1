# try.ps1 — evaluate Hermes Brain in a scratch vault, zero commitment.
#
# Copies the template into a fresh temp directory and opens it in Obsidian
# (if found), leaving your real Obsidian config, vault list, and any
# existing Hermes vault completely untouched. Nothing here is registered
# with the Hermes CLI, no cron jobs are set up -- this is look-before-you-
# install only. Run install.ps1 instead when you're ready to keep it.
$ErrorActionPreference = "Stop"

function Write-Bold($msg) { Write-Host $msg -ForegroundColor White }
function Write-Info($msg) { Write-Host "  $msg" }
function Write-Warn($msg) { Write-Host "  ! $msg" -ForegroundColor Yellow }
function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }

$TemplateRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path


Write-Host ""
Write-Bold "Hermes Brain -- try it (scratch vault, no install)"
Write-Info "Copies the template to a temp directory you can throw away any time."
Write-Info "Doesn't touch your real Obsidian config or register anything with Hermes."
Write-Host ""

$Scratch = Join-Path ([System.IO.Path]::GetTempPath()) "Hermes Brain (try)"
if (Test-Path $Scratch) {
  $Scratch = Join-Path ([System.IO.Path]::GetTempPath()) ("Hermes Brain (try) " + (Get-Date -Format "yyyyMMdd-HHmmss"))
}
New-Item -ItemType Directory -Path $Scratch -Force | Out-Null

Write-Info "Copying template to $Scratch ..."
Get-ChildItem -Path $TemplateRoot -Force | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
  Copy-Item -Path $_.FullName -Destination $Scratch -Recurse -Force
}
Write-Ok "Copied."

Write-Host ""
Write-Bold "Open it"
$obsidianCmd = Get-Command obsidian -ErrorAction SilentlyContinue
$obsidianExe = "$env:LOCALAPPDATA\Obsidian\Obsidian.exe"
$foundObsidian = $false
if ($obsidianCmd) { $foundObsidian = $true }
elseif (Test-Path $obsidianExe) { $foundObsidian = $true }

if ($foundObsidian) {
  $openNow = Read-Host "  Open in Obsidian now? [Y/n]"
  if ($openNow.ToLower() -ne "n") {
    if ($obsidianCmd) {
      Start-Process obsidian -ArgumentList "`"$Scratch`""
    } else {
      Start-Process $obsidianExe -ArgumentList "`"$Scratch`""
    }
    Write-Ok "Launched."
  }
} else {
  Write-Warn "Couldn't auto-detect Obsidian on PATH or in the default install location."
  Write-Info "Open Obsidian manually and choose `"Open folder as vault`" -> `"$Scratch`""
}

Write-Host ""
Write-Bold "Done."
Write-Info "Scratch vault: $Scratch"
Write-Info "This is a temp copy -- delete it any time with: Remove-Item -Recurse -Force `"$Scratch`""
Write-Info "Liked it? Run .\install.ps1 from this template to set up a real vault."
