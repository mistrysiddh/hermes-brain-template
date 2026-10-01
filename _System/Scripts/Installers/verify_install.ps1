#!/usr/bin/env pwsh
# verify_install.ps1
# Runs after installation to verify the Hermes Brain template is set up correctly.

$ErrorActionPreference = 'Stop'

Write-Host "🔍 Verifying your Hermes Brain install..." -ForegroundColor Cyan
Write-Host ""

$checks_passed = 0
$checks_total = 0

function Run-Check {
    param(
        [string]$Description,
        [scriptblock]$Command,
        [switch]$ExpectFailure
    )
    
    $checks_total++
    Write-Host -NoNewline "Checking: $Description... "
    try {
        & $Command | Out-Null
        if ($ExpectFailure) {
            Write-Host "❌ Unexpected success" -ForegroundColor Red
            return $false
        } else {
            Write-Host "✅ Pass" -ForegroundColor Green
            $checks_passed++
            return $true
        }
    } catch {
        if ($ExpectFailure) {
            Write-Host "✅ Expected failure" -ForegroundColor Green
            $checks_passed++
            return $true
        } else {
            Write-Host "❌ Failed" -ForegroundColor Red
            return $false
        }
    }
}

# Check 1: Basic vault structure exists
Run-Check -Description "Vault structure (01-Projects, 02-Areas, 03-Resources, 04-Archives, _System)" -Command {
    Test-Path "01-Projects" -and
    Test-Path "02-Areas" -and
    Test-Path "03-Resources" -and
    Test-Path "04-Archives" -and
    Test-Path "_System"
}

# Check 2: Key Obsidian plugins are present (Dataview, Smart Connections, Kanban)
Run-Check -Description "Obsidian plugins (dataview, smart-connections, kanban)" -Command {
    Test-Path ".obsidian/plugins/dataview" -and
    Test-Path ".obsidian/plugins/smart-connections" -and
    Test-Path ".obsidian/plugins/kanban"
}

# Check 3: MCP server is active
Run-Check -Description "MCP server status (should be active)" -Command {
    hermes-agent mcp-server status 2>$null | Select-String -Pattern "active" -Quiet
}

# Check 4: Memory promotion script --list runs without error
Run-Check -Description "Memory promotion script --list" -Command {
    python "_System/Scripts/promote_memory.py" --list 2>$null
}

# Check 5: User-Profile.md exists and has content (more than just template)
Run-Check -Description "User-Profile.md exists and has content" -Command {
    Test-Path "02-Areas/User-Profile.md" -and
    (Get-Item "02-Areas/User-Profile.md").Length -gt 50
}

# Check 6: .gitignore exists and ignores Daily/
Run-Check -Description ".gitignore exists and ignores Daily/" -Command {
    Select-Path -Path ".gitignore" -Pattern "^Daily/$" -Quiet
}

Write-Host ""
Write-Host "📊 Verification Summary: $checks_passed/$checks_total checks passed" -ForegroundColor Cyan

if ($checks_passed -eq $checks_total) {
    Write-Host "🎉 All checks passed! Your Hermes Brain install looks good." -ForegroundColor Green
    Write-Host "💡 Next steps: Try 'hermes-agent mcp-server start' and 'python _System/Scripts/promote_memory.py --review'" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "⚠️  Some checks failed. Review the output above for details." -ForegroundColor Yellow
    Write-Host "💡 Common issues:" -ForegroundColor Yellow
    Write-Host "   - MCP server not running: Start it with 'hermes-agent mcp-server start'" -ForegroundColor Yellow
    Write-Host "   - Missing plugins: Ensure you ran the installer fully" -ForegroundColor Yellow
    Write-Host "   - User-Profile.md too small: Edit it to add your details" -ForegroundColor Yellow
    exit 1
}