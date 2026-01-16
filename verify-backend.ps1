\
$ErrorActionPreference = "Stop"

function Get-BackendDir {
  $candidates = @("backend","api","server")
  foreach ($d in $candidates) {
    if (Test-Path $d) { return (Resolve-Path $d).Path }
  }
  return $null
}

$dir = Get-BackendDir
if (-not $dir) {
  Write-Host "No backend directory (backend/api/server) found."
  exit 0
}

Push-Location $dir
try {
  $hasPyproject = Test-Path "pyproject.toml"
  $hasReq = Test-Path "requirements.txt"

  $uv = Get-Command uv -ErrorAction SilentlyContinue
  $poetry = Get-Command poetry -ErrorAction SilentlyContinue

  if ($uv -and $hasPyproject) {
    Write-Host "== backend: install (uv sync) =="
    uv sync
    Write-Host "== backend: ruff check =="
    uv run ruff check .
    Write-Host "== backend: ruff format (check) =="
    uv run ruff format --check .
    Write-Host "== backend: pytest =="
    uv run pytest -q
  }
  elseif ($poetry -and $hasPyproject) {
    Write-Host "== backend: install (poetry) =="
    poetry install --no-interaction
    Write-Host "== backend: ruff check =="
    poetry run ruff check .
    Write-Host "== backend: ruff format (check) =="
    poetry run ruff format --check .
    Write-Host "== backend: pytest =="
    poetry run pytest -q
  }
  else {
    if (-not (Get-Command ruff -ErrorAction SilentlyContinue)) {
      throw "ruff is required but not found. Install via uv/poetry or pipx."
    }
    if ($hasReq) {
      Write-Host "== backend: install (pip requirements.txt) =="
      python -m pip install -U pip | Out-Null
      python -m pip install -r requirements.txt
    } elseif ($hasPyproject) {
      throw "pyproject.toml found but neither uv nor poetry is available."
    } else {
      Write-Host "No pyproject.toml/requirements.txt found; skipping install."
    }
    Write-Host "== backend: ruff check =="
    ruff check .
    Write-Host "== backend: ruff format (check) =="
    ruff format --check .
    Write-Host "== backend: pytest =="
    pytest -q
  }
}
finally {
  Pop-Location
}
