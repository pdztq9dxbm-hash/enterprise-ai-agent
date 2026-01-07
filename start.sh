#!/bin/bash

echo "=========================================="
echo "Enterprise AI Agent - Startup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}This script is designed for macOS${NC}"
    exit 1
fi

# Function to check if a service is running
check_service() {
    if pgrep -x "$1" > /dev/null; then
        echo -e "${GREEN}✓ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 is not running${NC}"
        return 1
    fi
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check PostgreSQL
if ! check_service "postgres"; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@15
    sleep 3
fi

# Check Redis
if ! command -v redis-server &> /dev/null; then
    echo "Redis not found. Installing..."
    brew install redis
fi

if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    brew services start redis
    sleep 2
fi

# Setup database
echo -e "\n${YELLOW}Setting up database...${NC}"
cd backend
source venv/bin/activate
python setup_db.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Database setup failed${NC}"
    exit 1
fi

# Check environment file
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create a .env file with your ANTHROPIC_API_KEY"
    exit 1
fi

# Check API key
if grep -q "your_openai_api_key_here" .env; then
    echo -e "${YELLOW}Warning: Please update OPENAI_API_KEY in .env file${NC}"
    echo "Get your key from: https://platform.openai.com/api-keys"
    read -p "Press Enter to continue or Ctrl+C to exit..."
fi

# Start backend
echo -e "\n${YELLOW}Starting backend server...${NC}"
cd backend
source venv/bin/activate
python -m uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to start
sleep 5

# Start frontend
echo -e "\n${YELLOW}Starting frontend...${NC}"
cd ../frontend
npm start &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

# Display information
echo -e "\n=========================================="
echo -e "${GREEN}✓ Enterprise AI Agent is running!${NC}"
echo "=========================================="
echo ""
echo "Backend API: http://localhost:8000"
echo "Frontend App: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Demo Credentials:"
echo "  Email: demo@example.com"
echo "  Password: demo123"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for Ctrl+C
trap "echo -e '\n${YELLOW}Shutting down...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Keep script running
wait