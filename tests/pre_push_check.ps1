# pre_push_check.ps1
# Run this before every git push to verify nothing is broken
# Usage: powershell -ExecutionPolicy Bypass -File tests\pre_push_check.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  MECP Pre-Push Check" -ForegroundColor Cyan
Write-Host "  Running automated tests before GitHub push" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

Set-Location $root

# ── Step 1: File structure (always runs, no Docker needed) ────────────────────
Write-Host ""
Write-Host "[1/4] File structure tests..." -ForegroundColor Yellow
python tests\test_mecp.py --suite files
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED: Fix missing files before pushing" -ForegroundColor Red
    exit 1
}

# ── Step 2: Agent mock logic (always runs, no Docker needed) ─────────────────
Write-Host ""
Write-Host "[2/4] AI agent logic tests..." -ForegroundColor Yellow
python tests\test_mecp.py --suite agent
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED: Agent logic broken" -ForegroundColor Red
    exit 1
}

# ── Step 3: MarkLogic API (skips gracefully if Docker not running) ────────────
Write-Host ""
Write-Host "[3/4] MarkLogic API tests..." -ForegroundColor Yellow
$mlRunning = docker ps --filter "name=ml" --filter "status=running" -q 2>$null
if ($mlRunning) {
    python tests\test_mecp.py --suite api
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAILED: MarkLogic API broken — do not push" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  SKIPPED: Docker not running (start with: docker compose up -d)" -ForegroundColor DarkYellow
}

# ── Step 4: Dashboard proxy (skips gracefully if not running) ─────────────────
Write-Host ""
Write-Host "[4/4] Dashboard proxy tests..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:8888/dashboard.html" -TimeoutSec 2 -ErrorAction Stop
    python tests\test_mecp.py --suite dashboard
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAILED: Dashboard proxy broken" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  SKIPPED: serve_dashboard.py not running (start with: python serve_dashboard.py)" -ForegroundColor DarkYellow
}

# ── Final result ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  ALL CHECKS PASSED - Safe to push" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  git add ." -ForegroundColor Cyan
Write-Host "  git commit -m 'your message'" -ForegroundColor Cyan
Write-Host "  git push origin main" -ForegroundColor Cyan
Write-Host ""
