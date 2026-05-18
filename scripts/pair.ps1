#!/usr/bin/env pwsh
# Pair this Watify install with WhatsApp.
#
# Two ways to pair:
#   1. Web UI - run scripts/dev-backend.ps1 and scripts/dev-frontend.ps1
#      in separate terminals, then visit http://localhost:3000/connect and
#      scan the QR with WhatsApp on your phone.
#   2. Terminal CLI - this script. Renders an ASCII QR in the console.
#      Useful for headless / SSH setups.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repoRoot "backend"
$script = Join-Path $backend "scripts/pair.py"

if (-not (Test-Path $script)) {
    Write-Error "pair.py not found at $script"
    exit 1
}

Set-Location $backend
Write-Host "Launching terminal pair flow. Open WhatsApp -> Linked devices -> Link a device, then scan the QR below." -ForegroundColor Cyan
uv run python scripts/pair.py
