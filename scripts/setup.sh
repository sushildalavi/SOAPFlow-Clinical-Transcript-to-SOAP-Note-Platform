#!/bin/bash
# SOAPFlow — One-command project setup
# Usage: bash scripts/setup.sh

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "\n${BLUE}${BOLD}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║        SOAPFlow Setup Script          ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"

# Check prerequisites
print_step "1. Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.11+ is required. Please install from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_success "Python $PYTHON_VERSION found"

if ! command -v node &> /dev/null; then
    echo "Error: Node.js 18+ is required. Please install from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION found"

# Backend setup
print_step "2. Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

echo "  Activating virtual environment..."
source venv/bin/activate

echo "  Installing Python dependencies..."
pip install -r requirements.txt -q
print_success "Backend dependencies installed"

if [ ! -f ".env" ]; then
    cp .env.example .env
    print_warn "Created backend/.env from .env.example"
    echo "  → Edit backend/.env to add your OpenAI or Anthropic API keys (optional)"
    echo "  → Demo mode works without any API keys"
else
    print_success "backend/.env already exists"
fi

cd ..

# Frontend setup
print_step "3. Setting up frontend..."
cd frontend

echo "  Installing npm dependencies..."
npm install --silent
print_success "Frontend dependencies installed"

cd ..

echo -e "\n${GREEN}${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║          Setup Complete!             ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}To start the application:${NC}"
echo ""
echo -e "  ${YELLOW}Terminal 1 (Backend):${NC}"
echo -e "    cd backend && source venv/bin/activate"
echo -e "    uvicorn app.main:app --reload --port 8000"
echo ""
echo -e "  ${YELLOW}Terminal 2 (Frontend):${NC}"
echo -e "    cd frontend && npm run dev"
echo ""
echo -e "  ${YELLOW}Or use the start script:${NC}"
echo -e "    bash scripts/start.sh"
echo ""
echo -e "  ${YELLOW}Or Docker:${NC}"
echo -e "    docker-compose up --build"
echo ""
echo -e "  Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "  API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
