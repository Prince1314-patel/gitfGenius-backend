# GiftGenius: Start PostgreSQL in Docker, create tables, verify (all via Docker).
# Prerequisite: Docker Desktop must be running.
# Usage: .\scripts\setup-postgres.ps1

$ErrorActionPreference = "Stop"
# Script lives in scripts/; project root is the parent of scripts/
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Checking Docker..." -ForegroundColor Cyan
try {
    docker info 2>&1 | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running or not installed." -ForegroundColor Red
    Write-Host "  - Start Docker Desktop (Windows/Mac), then run this script again." -ForegroundColor Yellow
    Write-Host "  - The error you saw (dockerDesktopLinuxEngine pipe) means the Docker daemon is not running." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting PostgreSQL in background (docker compose up -d)..." -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Waiting for Postgres to be ready (up to 30s)..." -ForegroundColor Cyan
$maxWait = 30
$waited = 0
do {
    Start-Sleep -Seconds 2
    $waited += 2
    $ok = docker exec giftgenius-postgres pg_isready -U prince1314 -d giftgenius 2>&1
    if ($LASTEXITCODE -eq 0) { break }
    if ($waited -ge $maxWait) {
        Write-Host "Postgres did not become ready in time." -ForegroundColor Red
        exit 1
    }
} while ($true)
Write-Host "Postgres is ready." -ForegroundColor Green

$migrationPath = Join-Path $ProjectRoot "migrations\001_create_tables.sql"
if (-not (Test-Path $migrationPath)) {
    Write-Host "Migration file not found: $migrationPath" -ForegroundColor Red
    exit 1
}

Write-Host "Creating tables (running migration inside container)..." -ForegroundColor Cyan
Get-Content $migrationPath -Raw | docker exec -i giftgenius-postgres psql -U prince1314 -d giftgenius -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Tables created." -ForegroundColor Green

Write-Host "Verifying tables (query run inside Docker only)..." -ForegroundColor Cyan
docker exec giftgenius-postgres psql -U prince1314 -d giftgenius -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('users','contacts','memories') ORDER BY table_name;"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done. PostgreSQL is running in the background and tables are set up." -ForegroundColor Green
