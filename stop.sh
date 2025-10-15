#!/bin/bash

echo "Stopping Whisper AI Backend services..."

# Stop FastAPI server
echo "Stopping FastAPI server..."
API_PID=$(lsof -t -i:${API_PORT:-8000})
if [ -n "$API_PID" ]; then
    kill "$API_PID"
    echo "  ✅ FastAPI server stopped"
else
    echo "  ℹ️  No FastAPI server running on port ${API_PORT:-8000}"
fi

# Stop Celery workers
echo "Stopping Celery workers..."
CELERY_PIDS=$(pgrep -f "celery -A celery_app worker")
if [ -n "$CELERY_PIDS" ]; then
    kill $CELERY_PIDS
    echo "  ✅ Celery workers stopped"
else
    echo "  ℹ️  No Celery workers running"
fi

# Stop any remaining main.py processes
echo "Stopping any remaining main.py processes..."
MAIN_PY_PIDS=$(pgrep -f "python3 main.py")
if [ -n "$MAIN_PY_PIDS" ]; then
    kill $MAIN_PY_PIDS
    echo "  ✅ main.py processes stopped"
else
    echo "  ℹ️  No main.py processes running"
fi

echo ""
echo "All services stopped!"

