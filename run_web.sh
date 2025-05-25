#!/bin/bash

# InfoBlox Network Import Web Application Launcher

echo "Starting InfoBlox Network Import Web Application..."
echo "=============================================="
echo ""

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

echo "Starting FastAPI server..."
echo "Web interface will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the web application
python app/web.py
