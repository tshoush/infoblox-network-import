#!/bin/bash

# InfoBlox Network Import - Quick Start Script

echo "InfoBlox Network Import Tool - Setup"
echo "===================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please edit .env file with your InfoBlox credentials"
fi

# Create required directories
mkdir -p uploads templates reports logs

echo ""
echo "Setup complete! To get started:"
echo ""
echo "1. Edit .env file with your InfoBlox credentials"
echo "2. Test connection: python app/cli.py test-connection"
echo "3. Import networks: python app/cli.py import-networks -f example_aws_networks.csv -s aws --dry-run"
echo ""
echo "For MCP server setup:"
echo "cd mcp-server && npm install && npm run build"
