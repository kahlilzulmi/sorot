Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $repoRoot 'frontend'

if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
    throw "frontend/package.json not found. Run this script from the repository root."
}

Set-Location $frontendDir
Write-Host "Starting backend + frontend..." -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Gray
Write-Host "Backend:  http://127.0.0.1:5000" -ForegroundColor Gray

npm run dev:all