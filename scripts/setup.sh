#!/bin/bash
# Quick Setup Script for CI/CD Optimization
# Run this script to set up everything quickly

set -e

echo "🚀 CI/CD Optimization - Quick Setup"
echo "===================================="
echo ""

# Check Python version
echo "1️⃣ Checking Python version..."
python --version || python3 --version
echo "✅ Python found"
echo ""

# Install dependencies
echo "2️⃣ Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Setup pre-commit hooks
echo "3️⃣ Setting up pre-commit hooks..."
pre-commit install
echo "✅ Pre-commit hooks installed"
echo ""

# Create .env from template
if [ ! -f .env ]; then
    echo "4️⃣ Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
    echo "✅ .env created"
else
    echo "4️⃣ .env already exists, skipping..."
fi
echo ""

# Validate installation
echo "5️⃣ Validating installation..."
python scripts/validate-implementation.py
echo ""

# Run local tests
echo "6️⃣ Running local tests (fast mode)..."
python scripts/test-local.py --fast
echo ""

echo "✨ Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run 'python scripts/test-local.py' before committing"
echo "3. Push to trigger CI/CD workflow"
echo "4. Monitor at http://localhost:3000 (Grafana)"
echo ""
echo "📚 Documentation: docs/CICD_QUICKSTART.md"
echo ""
