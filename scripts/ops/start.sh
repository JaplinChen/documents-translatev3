#!/bin/bash

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$PROJECT_ROOT/.venv"
BACKEND_PORT=5002
FRONTEND_PORT=5194
OLLAMA_URL="http://127.0.0.1:11434"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Environment Setup
setup_env() {
    if [ ! -d "$VENV_DIR" ]; then
        echo_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            echo_error "Failed to create venv. Please ensure python3 is installed."
            exit 1
        fi
        echo_info "Installing dependencies..."
        "$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements.txt"
    fi
}

# Helper: Check Port
check_port() {
    local port=$1
    local name=$2
    lsof -i :$port >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} $name: Running (port $port)"
    else
        echo -e "${RED}[X]${NC} $name: Not running"
    fi
}

# Helper: Start Backend
start_backend() {
    echo_info "[Backend] Starting in new window..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_ROOT' && source '$VENV_DIR/bin/activate' && uvicorn backend.main:app --reload --port $BACKEND_PORT --host 0.0.0.0\""
}

# Helper: Start Frontend
start_frontend() {
    echo_info "[Frontend] Starting in new window..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$FRONTEND_DIR' && npm run dev\""
}

# Helper: Stop Services
stop_services() {
    echo_info "Stopping services..."
    # Find PIDs listening on ports and kill them
    local backend_pid=$(lsof -t -i:$BACKEND_PORT)
    if [ ! -z "$backend_pid" ]; then
        kill $backend_pid
        echo_info "Backend stopped (PID $backend_pid)"
    else
        echo "Backend not running"
    fi

    local frontend_pid=$(lsof -t -i:$FRONTEND_PORT)
    if [ ! -z "$frontend_pid" ]; then
        kill $frontend_pid
        echo_info "Frontend stopped (PID $frontend_pid)"
    else
        echo "Frontend not running"
    fi
}

# Main Menu
show_menu() {
    clear
    echo "========================================"
    echo "   Documents Translate - macOS Startup  "
    echo "========================================"
    echo ""
    echo "   1. Start Backend + Frontend"
    echo "   2. Backend only (port $BACKEND_PORT)"
    echo "   3. Frontend only (port $FRONTEND_PORT)"
    echo "   4. Stop all services"
    echo "   5. Check status"
    echo "   6. Check Ollama"
    echo ""
    echo "   0. Exit"
    echo ""
    echo "========================================"
    read -p "Select [0-6]: " choice

    case $choice in
        1)
            start_backend
            start_frontend
            echo "Waiting for services..."
            sleep 5
            check_port $BACKEND_PORT "Backend"
            check_port $FRONTEND_PORT "Frontend"
            open "http://localhost:$FRONTEND_PORT"
            read -p "Press Enter to return..."
            ;;
        2)
            start_backend
            read -p "Press Enter to return..."
            ;;
        3)
            start_frontend
            open "http://localhost:$FRONTEND_PORT"
            read -p "Press Enter to return..."
            ;;
        4)
            stop_services
            read -p "Press Enter to return..."
            ;;
        5)
            check_port $BACKEND_PORT "Backend"
            check_port $FRONTEND_PORT "Frontend"
            read -p "Press Enter to return..."
            ;;
        6)
            curl -s -o /dev/null -w "%{http_code}" "$OLLAMA_URL" | grep "200" > /dev/null
            if [ $? -eq 0 ]; then
                echo_info "Ollama is running!"
            else
                echo_error "Cannot connect to Ollama at $OLLAMA_URL"
            fi
            read -p "Press Enter to return..."
            ;;
        0)
            exit 0
            ;;
        *)
            echo "Invalid choice"
            sleep 1
            ;;
    esac
}

# Main Execution
setup_env
while true; do
    show_menu
done
