#!/bin/bash
# Auto-generated Python code formatting script

set -e

echo "Formatting Python code..."

# Format with black
if command -v black &> /dev/null; then
    black .
    echo "✓ Black formatting complete"
else
    echo "⚠ Black not installed. Install with: pip install black"
fi

# Sort imports with isort
if command -v isort &> /dev/null; then
    isort .
    echo "✓ Import sorting complete"
else
    echo "⚠ isort not installed. Install with: pip install isort"
fi

# Lint with flake8
if command -v flake8 &> /dev/null; then
    flake8 . --max-line-length=120
    echo "✓ Linting complete"
else
    echo "⚠ flake8 not installed. Install with: pip install flake8"
fi

echo "All formatting checks complete!"
