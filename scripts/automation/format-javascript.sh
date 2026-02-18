#!/bin/bash
# Auto-generated JavaScript code formatter
set -e

echo "🎨 Formatting JavaScript/TypeScript code..."

# Check if prettier is installed
if ! command -v prettier &> /dev/null; then
    echo "Installing prettier..."
    npm install -g prettier
fi

# Format with prettier
echo "Running prettier..."
prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md}" \
    --ignore-path .gitignore

echo "✅ JavaScript code formatting complete!"
