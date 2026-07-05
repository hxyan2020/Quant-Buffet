# Quant Buffet local dev server (default port 3088; leaves 3000 free)
$ErrorActionPreference = "Stop"

$nodeDir = "${env:ProgramFiles}\nodejs"
if (Test-Path $nodeDir) {
  $env:Path = "$nodeDir;$env:Path"
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".env")) {
  Write-Host "Missing .env - copy .env.example to .env first." -ForegroundColor Yellow
  exit 1
}

function Test-PortInUse([int]$Port) {
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
  return $null -ne $conn
}

function Stop-StaleNodeOnPort([int]$Port) {
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
  if (-not $conn) { return $false }

  $ownerPid = $conn.OwningProcess
  $proc = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
  if (-not $proc) { return $false }

  $name = $proc.ProcessName.ToLowerInvariant()
  if ($name -eq "node" -or $name -eq "nodejs") {
    Write-Host "Port $Port is in use by Node (PID $ownerPid). Stopping stale dev server..." -ForegroundColor Yellow
    Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    return $true
  }

  Write-Host "Port $Port is in use by $($proc.ProcessName) (PID $pid), not Node." -ForegroundColor Red
  Write-Host "Close that app or pick another port manually: npx next dev -p 3090"
  return $false
}

function Find-FreePort([int]$StartPort, [int]$MaxTries = 20) {
  for ($p = $StartPort; $p -lt ($StartPort + $MaxTries); $p++) {
    if (-not (Test-PortInUse $p)) { return $p }
  }
  return $null
}

# Stop accidental Next on 3000 (stale Prisma client causes strategy-library crashes)
if (Test-PortInUse 3000) {
  Stop-StaleNodeOnPort 3000 | Out-Null
}

Write-Host "Syncing Prisma client..."
npx prisma generate 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Prisma generate failed. Close all Node terminals and run: npx prisma generate" -ForegroundColor Red
  exit 1
}

$preferredPort = 3088
if (Test-PortInUse $preferredPort) {
  $stopped = Stop-StaleNodeOnPort $preferredPort
  if (-not $stopped -and (Test-PortInUse $preferredPort)) {
    $preferredPort = Find-FreePort 3089
    if (-not $preferredPort) {
      Write-Host "No free port found between 3089-3108." -ForegroundColor Red
      exit 1
    }
    Write-Host "Using alternate port $preferredPort because 3088 is still busy." -ForegroundColor Yellow
  }
}

$port = $preferredPort

Write-Host ""
Write-Host "Quant Buffet dev server" -ForegroundColor Cyan
Write-Host ("  Local:   http://localhost:{0}" -f $port) -ForegroundColor Green

$lan = $null
try {
  $lan = (
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
    Where-Object {
      $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown"
    } |
    Select-Object -First 1
  ).IPAddress
} catch {
  $lan = $null
}

if ($lan) {
  Write-Host ("  Network: http://{0}:{1}" -f $lan, $port) -ForegroundColor Green
}

Write-Host "  Port 3000 is intentionally unused." -ForegroundColor DarkGray
Write-Host ""

$env:PORT = "$port"
$env:AUTH_URL = "http://localhost:$port"
npx next dev -p $port
