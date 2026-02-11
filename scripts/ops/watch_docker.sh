#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================"
echo "  Docker Watch (Auto Update)   "
echo "================================"

echo "[1/2] Starting containers..."
docker compose up -d backend frontend

echo "[2/2] Watching for changes..."
echo "  - frontend/src -> rebuild frontend"
echo "  - frontend/public -> rebuild frontend"
echo "  - backend -> sync/reload"
echo "  (Press Ctrl+C to stop)"

docker compose watch
