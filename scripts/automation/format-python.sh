#!/bin/bash
# Auto-generated Python code formatter
set -e

echo "🎨 Formatting Python code..."

# Check if black is installed
if ! command -v black &> /dev/null; then
    echo "Installing black..."
    pip install black
fi

# Check if isort is installed
if ! command -v isort &> /dev/null; then
    echo "Installing isort..."
    pip install isort
fi

# Format with black
echo "Running black..."
black . --line-length 100 --exclude '/(\.git|\.venv|venv|__pycache__|\.tox|dist|build)/'

# Sort imports with isort
echo "Running isort..."
isort . --profile black --skip-gitignore

echo "✅ Python code formatting complete!"
