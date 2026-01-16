\
$ErrorActionPreference = "Stop"

function Get-FrontendDir {
  $candidates = @("web","frontend","ui")
  foreach ($d in $candidates) {
    if (Test-Path $d) { return (Resolve-Path $d).Path }
  }
  return $null
}

function Has-Script($pkgPath, $name) {
  $pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
  return ($null -ne $pkg.scripts) -and ($pkg.scripts.PSObject.Properties.Name -contains $name)
}

$dir = Get-FrontendDir
if (-not $dir) {
  Write-Host "No frontend directory (web/frontend/ui) found."
  exit 0
}

Push-Location $dir
try {
  if (-not (Test-Path "package.json")) {
    Write-Host "package.json not found in frontend dir; skipping."
    exit 0
  }

  $pm = "npm"
  if (Test-Path "pnpm-lock.yaml") { $pm = "pnpm" }
  elseif (Test-Path "yarn.lock") { $pm = "yarn" }

  if ($pm -eq "pnpm") {
    if (Get-Command corepack -ErrorAction SilentlyContinue) { corepack enable | Out-Null }
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) { throw "pnpm-lock.yaml found but pnpm is not installed." }
    pnpm install --frozen-lockfile
    $run = { param($s) pnpm -s run $s }
  } elseif ($pm -eq "yarn") {
    if (Get-Command corepack -ErrorAction SilentlyContinue) { corepack enable | Out-Null }
    if (-not (Get-Command yarn -ErrorAction SilentlyContinue)) { throw "yarn.lock found but yarn is not installed." }
    yarn install --frozen-lockfile
    $run = { param($s) yarn -s $s }
  } else {
    if (Test-Path "package-lock.json") { npm ci } else { npm install }
    $run = { param($s) npm run -s $s }
  }

  $pkgPath = "package.json"

  if (Has-Script $pkgPath "lint") {
    Write-Host "== frontend: lint =="
    & $run "lint"
  } else {
    Write-Host "== frontend: lint (skipped; no script) =="
  }

  if (Has-Script $pkgPath "test") {
    Write-Host "== frontend: test =="
    & $run "test"
  } else {
    Write-Host "== frontend: test (skipped; no script) =="
  }

  Write-Host "== frontend: build =="
  $isNext = (Test-Path "next.config.js") -or (Test-Path "next.config.mjs") -or (Test-Path "next.config.ts")
  if (Has-Script $pkgPath "build") {
    & $run "build"
  } else {
    if ($isNext) {
      npx -y next build
    } else {
      npx -y vite build
    }
  }
}
finally {
  Pop-Location
}
