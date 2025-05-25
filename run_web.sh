#!/bin/bash

# InfoBlox Network Import Web Application Launcher

echo "Starting InfoBlox Network Import Web Application..."
echo "=============================================="
echo ""

# Check if port is already in use
PORT=${PORT:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port $PORT is already in use!"
    echo ""
    echo "Options:"
    echo "1. Kill the existing process: kill $(lsof -t -i:$PORT)"
    echo "2. Use a different port: PORT=8001 ./run_web.sh"
    echo ""
    read -p "Kill existing process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $(lsof -t -i:$PORT)
        sleep 1
        echo "✓ Killed existing process"
    else
        echo "Exiting. Use: PORT=8001 ./run_web.sh to use a different port"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    ./setup.sh
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your InfoBlox credentials"
    echo ""
fi

# Create required directories
mkdir -p uploads reports logs templates

echo "Starting FastAPI server on port $PORT..."
echo "Web interface will be available at: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the web application
uvicorn app.web:app --host 0.0.0.0 --port $PORT
