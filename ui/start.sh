#!/bin/bash

# ToggleHealth Multi-Agent Assistant - Start Script

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ToggleHealth Multi-Agent Assistant                          ║"
echo "║  Starting backend and frontend servers...                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

