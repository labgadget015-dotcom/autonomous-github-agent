#!/bin/bash
# Auto-generated code linter
set -e

echo "🔍 Running linters..."

EXIT_CODE=0

# Python linting
if ls *.py 2>/dev/null || [ -d "scripts" ] || [ -d "src" ]; then
    echo "Linting Python code..."
    
    # flake8
    if command -v flake8 &> /dev/null; then
        echo "Running flake8..."
        flake8 . --max-line-length=100 --exclude=.git,__pycache__,.venv,venv || EXIT_CODE=1
    fi
    
    # pylint
    if command -v pylint &> /dev/null; then
        echo "Running pylint..."
        find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" | xargs pylint || EXIT_CODE=1
    fi
    
    # mypy
    if command -v mypy &> /dev/null; then
        echo "Running mypy..."
        mypy . --ignore-missing-imports || EXIT_CODE=1
    fi
fi

# JavaScript linting
if [ -f "package.json" ]; then
    if command -v npm &> /dev/null; then
        if grep -q "eslint" package.json; then
            echo "Running ESLint..."
            npm run lint || EXIT_CODE=1
        fi
    fi
fi

# Security linting
if command -v bandit &> /dev/null; then
    echo "Running security scan with bandit..."
    bandit -r . -x ./.venv,./venv,./tests || EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All linting checks passed!"
else
    echo "❌ Some linting checks failed"
fi

exit $EXIT_CODE
