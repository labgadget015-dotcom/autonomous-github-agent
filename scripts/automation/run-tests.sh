#!/bin/bash
# Auto-generated test runner
set -e

echo "🧪 Running tests..."

# Check if pytest is installed
if ! python -m pytest --version &> /dev/null; then
    echo "Installing pytest..."
    pip install pytest pytest-cov pytest-xdist
fi

# Run tests with coverage
echo "Running pytest with coverage..."
python -m pytest \
    --verbose \
    --cov=. \
    --cov-report=html \
    --cov-report=term \
    --cov-report=xml \
    -n auto \
    tests/

# Check coverage threshold
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
THRESHOLD=80

echo ""
if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
    echo "⚠️  Coverage ($COVERAGE%) is below threshold ($THRESHOLD%)"
    exit 1
else
    echo "✅ Coverage ($COVERAGE%) meets threshold ($THRESHOLD%)"
fi

echo ""
echo "Coverage report: htmlcov/index.html"
