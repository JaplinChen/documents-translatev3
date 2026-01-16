#!/usr/bin/env bash
set -euo pipefail

if [ -d backend ]; then cd backend
elif [ -d api ]; then cd api
elif [ -d server ]; then cd server
else
  echo "No backend directory (backend/api/server) found."
  exit 0
fi

python -m pip install -U pip >/dev/null 2>&1 || true

if command -v uv >/dev/null 2>&1 && [ -f pyproject.toml ]; then
  echo "== backend: install (uv) =="
  uv sync
  echo "== backend: ruff check =="
  uv run ruff check .
  echo "== backend: ruff format (check) =="
  uv run ruff format --check .
  echo "== backend: pytest =="
  uv run pytest -q
elif command -v poetry >/dev/null 2>&1 && [ -f pyproject.toml ]; then
  echo "== backend: install (poetry) =="
  poetry install --no-interaction
  echo "== backend: ruff check =="
  poetry run ruff check .
  echo "== backend: ruff format (check) =="
  poetry run ruff format --check .
  echo "== backend: pytest =="
  poetry run pytest -q
else
  echo "Neither uv nor poetry available for pyproject workflow."
  if [ -f requirements.txt ]; then
    python -m pip install -r requirements.txt
  fi
  ruff check .
  ruff format --check .
  pytest -q
fi
