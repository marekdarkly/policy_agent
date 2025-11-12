#!/bin/bash

# ToggleHealth Multi-Agent Assistant - Start Script

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ToggleHealth Multi-Agent Assistant                          ║"
echo "║  Starting backend and frontend servers...                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Kill any existing servers on port 8000 and 3000
echo "🧹 Cleaning up any existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Check if dependencies are installed
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend"
    npm install
fi

# Activate venv and check backend dependencies
cd "$PROJECT_ROOT"
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'make setup' first."
    exit 1
fi

source venv/bin/activate

# Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    pip install -r "$SCRIPT_DIR/backend/requirements.txt"
fi

# Start backend in background
echo "🚀 Starting FastAPI backend on port 8000..."
cd "$SCRIPT_DIR/backend"
python server.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend
echo "🚀 Starting React frontend on port 3000..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

