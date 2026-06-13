#!/bin/bash
# Auto-generated Python environment setup script

set -e

echo "Setting up Python development environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
# shellcheck source=/dev/null
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
fi

# Install development dependencies
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
    echo "✓ Development dependencies installed"
fi

# Setup pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Setting up pre-commit hooks..."
    pip install pre-commit
    pre-commit install
    echo "✓ Pre-commit hooks installed"
fi

echo ""
echo "Setup complete! To activate the environment, run:"
echo "  source venv/bin/activate"
