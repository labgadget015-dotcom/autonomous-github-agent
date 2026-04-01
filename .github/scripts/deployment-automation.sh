#!/bin/bash

################################################################################
# Autonomous GitHub Agent - One-Click Deployment Automation
# This script automates the deployment of the Autonomous GitHub Agent
# Supports: Self-hosted, Docker, Kubernetes, Cloud platforms
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/labgadget015-dotcom/autonomous-github-agent"
DEFAULT_BRANCH="main"
INSTALL_DIR="$HOME/autonomous-github-agent"

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════"
echo "  Autonomous GitHub Agent - Deployment Automation"
echo "  AI-Powered GitHub Automation with 90% Token Cost Reduction"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Function: Print info message
info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Function: Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function: Print warning message
warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function: Print error message and exit
error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    warn "Running as root is not recommended. Consider using a regular user."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect OS
info "Detecting operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    success "Detected: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    success "Detected: macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    success "Detected: Windows"
else
    error "Unsupported operating system: $OSTYPE"
fi

# Check dependencies
info "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    error "Python 3 is required but not installed. Please install Python 3.9+"
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
success "Python $PYTHON_VERSION found"

if ! command -v git &> /dev/null; then
    error "Git is required but not installed. Please install Git"
fi
success "Git found"

if ! command -v pip3 &> /dev/null; then
    error "pip3 is required but not installed. Please install pip3"
fi
success "pip3 found"

# Deployment mode selection
info "Select deployment mode:"
echo "1) Self-hosted (Local installation)"
echo "2) Docker (Containerized deployment)"
echo "3) Kubernetes (K8s cluster deployment)"
echo "4) Cloud Platform (AWS/GCP/Azure)"
read -p "Enter choice [1-4]: " DEPLOY_MODE

case $DEPLOY_MODE in
    1)
        info "Selected: Self-hosted deployment"
        
        # Clone or update repository
        if [ -d "$INSTALL_DIR" ]; then
            info "Updating existing installation..."
            cd "$INSTALL_DIR"
            git pull origin $DEFAULT_BRANCH
        else
            info "Cloning repository..."
            git clone "$REPO_URL" "$INSTALL_DIR"
            cd "$INSTALL_DIR"
        fi
        success "Repository ready"
        
        # Create virtual environment
        info "Setting up Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        success "Virtual environment created"
        
        # Install dependencies
        info "Installing Python dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt 2>/dev/null || pip install aiohttp anthropic openai requests pyyaml pylint flake8 bandit pytest
        success "Dependencies installed"
        
        # Setup environment variables
        info "Configuring environment variables..."
        if [ ! -f ".env" ]; then
            cp .env.example .env
            info "Created .env file. Please edit it with your API keys:"
            echo "  - GITHUB_TOKEN (required)"
            echo "  - OPENAI_API_KEY (optional, for cloud LLM)"
            echo "  - ANTHROPIC_API_KEY (optional, for cloud LLM)"
        fi
        
        # Setup local LLM (optional)
        read -p "Install local LLM (Ollama) for 90% cost savings? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "Installing Ollama..."
            if [[ "$OS" == "linux" ]]; then
                curl -fsSL https://ollama.com/install.sh | sh
            elif [[ "$OS" == "macos" ]]; then
                brew install ollama
            fi
            
            info "Pulling recommended model (deepseek-coder-v2)..."
            ollama pull deepseek-coder-v2:16b-lite-instruct-q4_0
            success "Local LLM installed and ready"
        fi
        
        success "Self-hosted deployment complete!"
        echo ""
        info "To start using the agent:"
        echo "  1. Edit .env file with your credentials"
        echo "  2. Run: source venv/bin/activate"
        echo "  3. Test: python .github/scripts/async_parallel_analyzer.py"
        ;;
        
    2)
        info "Selected: Docker deployment"
        
        # Check Docker
        if ! command -v docker &> /dev/null; then
            error "Docker is required. Install from: https://docs.docker.com/get-docker/"
        fi
        success "Docker found"
        
        # Clone repository if needed
        if [ ! -d "$INSTALL_DIR" ]; then
            git clone "$REPO_URL" "$INSTALL_DIR"
        fi
        cd "$INSTALL_DIR"
        
        # Build Docker image
        info "Building Docker image..."
        docker build -t autonomous-github-agent:latest .
        success "Docker image built"
        
        # Setup environment
        if [ ! -f ".env" ]; then
            cp .env.example .env
            warn "Please edit .env file with your API keys before running"
        fi
        
        # Run container
        info "Starting container..."
        docker run -d \
            --name autonomous-github-agent \
            --env-file .env \
            -v $(pwd)/.github:/app/.github \
            -p 8080:8080 \
            autonomous-github-agent:latest
        
        success "Docker deployment complete!"
        echo ""
        info "Container is running. Check status with:"
        echo "  docker ps"
        echo "  docker logs autonomous-github-agent"
        ;;
        
    3)
        info "Selected: Kubernetes deployment"
        
        # Check kubectl
        if ! command -v kubectl &> /dev/null; then
            error "kubectl is required. Install from: https://kubernetes.io/docs/tasks/tools/"
        fi
        success "kubectl found"
        
        # Clone repository
        if [ ! -d "$INSTALL_DIR" ]; then
            git clone "$REPO_URL" "$INSTALL_DIR"
        fi
        cd "$INSTALL_DIR"
        
        # Create namespace
        info "Creating Kubernetes namespace..."
        kubectl create namespace autonomous-agent || true
        
        # Create secrets
        info "Setting up secrets..."
        read -p "Enter GitHub Token: " GITHUB_TOKEN
        kubectl create secret generic github-credentials \
            --from-literal=token=$GITHUB_TOKEN \
            -n autonomous-agent || true
        
        # Apply manifests
        info "Deploying to Kubernetes..."
        kubectl apply -f k8s/ -n autonomous-agent
        
        success "Kubernetes deployment complete!"
        echo ""
        info "Check deployment status:"
        echo "  kubectl get pods -n autonomous-agent"
        echo "  kubectl logs -f deployment/autonomous-agent -n autonomous-agent"
        ;;
        
    4)
        info "Selected: Cloud Platform deployment"
        echo "Select cloud provider:"
        echo "1) AWS (ECS/EKS)"
        echo "2) Google Cloud (Cloud Run/GKE)"
        echo "3) Azure (Container Instances/AKS)"
        read -p "Enter choice [1-3]: " CLOUD_CHOICE
        
        case $CLOUD_CHOICE in
            1)
                info "AWS deployment - Please ensure AWS CLI is configured"
                # Add AWS-specific deployment logic
                warn "AWS deployment requires additional setup. See docs/CLOUD_DEPLOYMENT.md"
                ;;
            2)
                info "Google Cloud deployment - Please ensure gcloud CLI is configured"
                warn "GCP deployment requires additional setup. See docs/CLOUD_DEPLOYMENT.md"
                ;;
            3)
                info "Azure deployment - Please ensure Azure CLI is configured"
                warn "Azure deployment requires additional setup. See docs/CLOUD_DEPLOYMENT.md"
                ;;
            *)
                error "Invalid choice"
                ;;
        esac
        ;;
        
    *)
        error "Invalid deployment mode"
        ;;
esac

echo ""
echo -e "${GREEN}"
echo "═══════════════════════════════════════════════════════════════"
echo "  Deployment Complete! 🚀"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""
info "Next steps:"
echo "  1. Configure your .env file with API credentials"
echo "  2. Test the installation with sample workflows"
echo "  3. Integrate with your GitHub repositories"
echo "  4. Monitor cost savings in the dashboard"
echo ""
info "Documentation: https://github.com/labgadget015-dotcom/autonomous-github-agent/tree/main/docs"
info "Support: Open an issue on GitHub"
echo ""
success "Happy automating! 🤖"
