#!/bin/bash
# VayuSense — One-command startup script
# Starts: Docker (DB + Redis), FastAPI backend, React frontend

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${CYAN}"
echo "  🌬️  VayuSense — Urban Air Quality Intelligence"
echo "  Starting all services..."
echo -e "${NC}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Docker ──────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Starting TimescaleDB + Redis...${NC}"
cd "$ROOT_DIR"
docker-compose up -d
sleep 3
echo -e "${GREEN}  ✅ Database + Redis running${NC}"

# ── 2. Python venv ─────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/4] Setting up Python environment...${NC}"
cd "$ROOT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}  ✅ Python environment ready${NC}"

# ── 3. Backend ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/4] Starting FastAPI backend on :8000...${NC}"
cd "$ROOT_DIR/backend"
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 2
echo -e "${GREEN}  ✅ Backend running at http://localhost:8000${NC}"
echo -e "     API docs: http://localhost:8000/docs"

# ── 4. Frontend ────────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Starting React dashboard on :5173...${NC}"
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
sleep 2
echo -e "${GREEN}  ✅ Dashboard running at http://localhost:5173${NC}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  🌬️  VayuSense is LIVE"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Dashboard:  http://localhost:5173"
echo -e "  API:        http://localhost:8000"
echo -e "  API Docs:   http://localhost:8000/docs"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker-compose stop; exit 0" INT
wait
