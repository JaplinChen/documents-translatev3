#!/bin/bash
# Docker Deployment Script for PPT Translate
# This script starts Ollama with correct binding and launches Docker containers

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================"
echo "  documents-translatev3 - Docker Setup  "
echo "================================"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Stop existing containers
echo "[1/4] Stopping existing containers..."
docker compose down 2>/dev/null || true

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "[2/4] Starting Ollama with Docker-compatible binding..."
    # Kill existing Ollama processes
    pkill -f "ollama serve" 2>/dev/null || true
    sleep 1

    # Start Ollama with 0.0.0.0 binding (allows Docker access)
    OLLAMA_HOST=0.0.0.0 ollama serve &
    OLLAMA_PID=$!
    echo "    Ollama started (PID: $OLLAMA_PID)"
    sleep 3
else
    echo "[2/4] Ollama not installed, skipping..."
    echo "    Note: Ollama features will not be available"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "    Created .env. Please update it with your API keys if needed."
fi

# 建置並啟動容器
echo "[3/4] 建置並啟動 Docker 容器..."
docker compose up -d --build

# Wait for health check
echo "[4/4] Waiting for services to be healthy..."
sleep 5

# Check status
echo
echo "================================"
echo "         Service Status         "
echo "================================"
docker compose ps
echo
echo "================================"
echo "  Access URLs                   "
echo "================================"
echo "  Frontend: http://localhost:5194"
echo "  Backend:  http://localhost:5002"
echo "  API Docs: http://localhost:5002/docs"
echo "================================"
echo
echo "Container Logs summary:"
docker compose logs --tail=20
echo
echo "Use 'docker compose logs -f' to view full logs"
echo "Use 'docker compose down' to stop all services"
