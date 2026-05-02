#!/bin/bash
# SOAPFlow — Start both backend and frontend concurrently
# Usage: bash scripts/start.sh

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BOLD}Starting SOAPFlow...${NC}"

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Backend virtual environment not found. Running setup first..."
    bash scripts/setup.sh
fi

# Check if node_modules exist
if [ ! -d "frontend/node_modules" ]; then
    echo "Frontend dependencies not installed. Running setup first..."
    bash scripts/setup.sh
fi

echo -e "\n${BOLD}Starting services:${NC}"
echo -e "  Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "  Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "  API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "\nPress Ctrl+C to stop all services.\n"

# Start backend in background
(cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000 2>&1 | sed 's/^/[backend] /') &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start frontend
(cd frontend && npm run dev 2>&1 | sed 's/^/[frontend] /') &
FRONTEND_PID=$!

# Wait and handle Ctrl+C gracefully
trap "echo -e '\n${BOLD}Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait $BACKEND_PID $FRONTEND_PID
