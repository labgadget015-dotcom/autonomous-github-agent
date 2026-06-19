#!/bin/bash

# Development Environment Setup Script
# This script sets up a local development environment for the autonomous-github-agent

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Check Python version
check_python() {
    print_header "Checking Python Installation"

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11 or later."
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"

    # Check if version is 3.11 or later
    REQUIRED_VERSION="3.11.0"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_warning "Python 3.11+ is recommended. You have $PYTHON_VERSION"
    fi
}

# Create and activate virtual environment
setup_virtualenv() {
    print_header "Setting Up Virtual Environment"

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping creation."
    else
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    print_info "To activate the virtual environment, run:"
    print_info "  source venv/bin/activate  (Linux/Mac)"
    print_info "  venv\\Scripts\\activate     (Windows)"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"

    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        # shellcheck source=/dev/null
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        # shellcheck source=/dev/null
        source venv/Scripts/activate
    else
        print_error "Virtual environment not found. Please create it first."
        exit 1
    fi

    print_info "Installing Python packages..."
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt

    print_info "Installing development dependencies..."
    pip install pytest pytest-cov pytest-xdist
    pip install black isort flake8 pylint bandit radon
    pip install pre-commit

    print_success "All dependencies installed"
}

# Setup environment file
setup_env_file() {
    print_header "Setting Up Environment File"

    if [ -f ".env" ]; then
        print_warning ".env file already exists. Skipping."
        print_info "If you want to reset it, run: cp .env.development .env"
    else
        print_info "Creating .env from .env.development..."
        cp .env.development .env
        print_success ".env file created"
        print_warning "Please edit .env and add your GitHub token and other credentials"
    fi
}

# Install pre-commit hooks
install_precommit() {
    print_header "Installing Pre-commit Hooks"

    if [ -f "venv/bin/activate" ]; then
        # shellcheck source=/dev/null
        source venv/bin/activate
    fi

    print_info "Installing pre-commit hooks..."
    pre-commit install
    print_success "Pre-commit hooks installed"

    print_info "Running pre-commit on all files..."
    pre-commit run --all-files || true
    print_success "Pre-commit check complete"
}

# Create necessary directories
create_directories() {
    print_header "Creating Necessary Directories"

    mkdir -p reports
    mkdir -p .github/badges
    mkdir -p logs
    mkdir -p tmp

    print_success "Directories created"
}

# Run initial tests
run_tests() {
    print_header "Running Initial Tests"

    if [ -f "venv/bin/activate" ]; then
        # shellcheck source=/dev/null
        source venv/bin/activate
    fi

    print_info "Running test suite..."
    if pytest -n auto --tb=short -v; then
        print_success "All tests passed!"
    else
        print_warning "Some tests failed. This is okay for initial setup."
        print_info "You can fix failing tests as you develop."
    fi
}

# Display final instructions
show_final_instructions() {
    print_header "Setup Complete! 🎉"

    echo -e "Your development environment is ready. Next steps:\n"
    echo -e "1. Activate the virtual environment:"
    echo -e "   ${GREEN}source venv/bin/activate${NC} (Linux/Mac)"
    echo -e "   ${GREEN}venv\\Scripts\\activate${NC} (Windows)\n"

    echo -e "2. Edit ${GREEN}.env${NC} and add your credentials:"
    echo -e "   - GITHUB_TOKEN (required)"
    echo -e "   - Other API keys as needed\n"

    echo -e "3. Run the local test script:"
    echo -e "   ${GREEN}python scripts/test-local.py${NC}\n"

    echo -e "4. Start developing:"
    echo -e "   - Write code in ${GREEN}.github/scripts/${NC}"
    echo -e "   - Run tests: ${GREEN}pytest -n auto${NC}"
    echo -e "   - Format code: ${GREEN}black . && isort .${NC}"
    echo -e "   - Check quality: ${GREEN}make lint${NC}\n"

    echo -e "5. Before committing:"
    echo -e "   - Pre-commit hooks will run automatically"
    echo -e "   - Or run manually: ${GREEN}pre-commit run --all-files${NC}\n"

    echo -e "6. Useful commands:"
    echo -e "   - ${GREEN}make help${NC} - Show all available commands"
    echo -e "   - ${GREEN}make test${NC} - Run tests"
    echo -e "   - ${GREEN}make lint${NC} - Run linters"
    echo -e "   - ${GREEN}make format${NC} - Auto-format code\n"

    print_info "Documentation: Check README.md and CONTRIBUTING.md"
    print_info "Need help? Open an issue on GitHub"
}

# Main setup flow
main() {
    print_header "Autonomous GitHub Agent - Development Setup"
    print_info "This script will set up your local development environment\n"

    # Run all setup steps
    check_python
    setup_virtualenv
    install_dependencies
    setup_env_file
    create_directories
    install_precommit

    # Ask if user wants to run tests
    echo -e "\n${YELLOW}Do you want to run initial tests? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        run_tests
    else
        print_info "Skipping initial tests. You can run them later with: pytest"
    fi

    show_final_instructions
}

# Run main function
main
