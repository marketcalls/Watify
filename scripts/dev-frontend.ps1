#!/usr/bin/env pwsh
# Start the Watify frontend (Next.js dev server) on http://localhost:3000.
# Requires the backend running on :8000 for /api/* calls to succeed.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $repoRoot "frontend"

if (-not (Test-Path $frontend)) {
    Write-Error "frontend directory not found at $frontend"
    exit 1
}

Set-Location $frontend
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "node_modules missing -- running npm install first" -ForegroundColor Yellow
    npm install --no-audit --no-fund
}
Write-Host "Starting Watify frontend on http://localhost:3000 (Ctrl-C to stop)" -ForegroundColor Cyan
npm run dev
