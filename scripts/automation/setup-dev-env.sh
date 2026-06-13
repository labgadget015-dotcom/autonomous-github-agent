#!/bin/bash
# Auto-generated development environment setup
set -e

echo "🛠️  Setting up development environment..."

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "Detected OS: $OS"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python $(python3 --version) found"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
# shellcheck source=/dev/null
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Install pre-commit hooks if available
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
fi

# Check for Node.js dependencies
if [ -f "package.json" ]; then
    if command -v npm &> /dev/null; then
        echo "Installing Node.js dependencies..."
        npm install
    else
        echo "⚠️  package.json found but npm not installed"
    fi
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate  # Linux/macOS"
# shellcheck disable=SC2028
echo '  .venv\Scripts\activate     # Windows'
