#!/bin/bash
# Quick start script for Autonomous GitHub Agent (Linux/macOS)

set -e

echo "================================================"
echo "Autonomous GitHub Agent - Docker Quick Start"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "[1/5] Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo ""
        echo "IMPORTANT: Please edit .env file with your configuration!"
        echo "Run: nano .env (or use your preferred editor)"
        read -r -p "Press Enter to continue after editing .env..."
    else
        echo "ERROR: .env.example not found"
        exit 1
    fi
else
    echo ".env file found"
fi

echo ""
echo "[2/5] Creating context.json if needed..."
if [ ! -f "context.json" ]; then
    if [ -f "context.json.example" ]; then
        cp context.json.example context.json
        echo "Created context.json from example"
    fi
fi

echo ""
echo "[3/5] Building Docker image..."
docker-compose build

echo ""
echo "[4/5] Starting containers..."
docker-compose up -d

echo ""
echo "[5/5] Checking status..."
docker-compose ps

echo ""
echo "================================================"
echo "Setup complete!"
echo "================================================"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f agent    - View logs"
echo "  docker-compose down             - Stop containers"
echo "  docker-compose restart          - Restart containers"
echo ""
echo "Or use the Makefile:"
echo "  make logs    - View logs"
echo "  make down    - Stop containers"
echo "  make restart - Restart containers"
echo ""
