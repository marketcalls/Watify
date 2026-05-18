#!/usr/bin/env pwsh
# Start the Watify backend (FastAPI + uvicorn) on http://localhost:8000.
# Reads config from backend/.env (optional) via pydantic-settings.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repoRoot "backend"

if (-not (Test-Path $backend)) {
    Write-Error "backend directory not found at $backend"
    exit 1
}

Set-Location $backend
Write-Host "Starting Watify backend on http://localhost:8000 (Ctrl-C to stop)" -ForegroundColor Cyan
uv run uvicorn app.main:app --reload --port 8000
