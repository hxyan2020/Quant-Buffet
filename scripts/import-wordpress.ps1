# Import WordPress WXR export into local SQLite (Prisma)
$ErrorActionPreference = "Stop"

$nodeDir = "${env:ProgramFiles}\nodejs"
if (Test-Path $nodeDir) {
  $env:Path = "$nodeDir;$env:Path"
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$wxr = Join-Path $projectRoot "data\quantbuffet.WordPress.xml"
if (-not (Test-Path $wxr)) {
  Write-Host "Missing export: data\quantbuffet.WordPress.xml" -ForegroundColor Red
  Write-Host "Copy your WordPress Tools > Export file there first."
  exit 1
}

Write-Host "Dry-run preview (no DB writes)..." -ForegroundColor Cyan
npx tsx scripts/import-wxr.ts --dry-run
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$confirm = Read-Host "Import into database? This upserts all posts. Type YES to continue"
if ($confirm -ne "YES") {
  Write-Host "Cancelled."
  exit 0
}

Write-Host "Importing (replace existing strategies)..." -ForegroundColor Cyan
npx tsx scripts/import-wxr.ts --replace
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Import finished. Start the site with: .\scripts\run-dev.ps1" -ForegroundColor Green
