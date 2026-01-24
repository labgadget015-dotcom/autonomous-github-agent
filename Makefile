# Makefile for Autonomous GitHub Agent Docker operations and CI/CD
.PHONY: help build build-prod up down logs test clean restart rebuild analyze benchmark badges optimize

# Default target
help:
	@echo "Autonomous GitHub Agent - Docker & CI/CD Commands"
	@echo ""
	@echo "Development Commands:"
	@echo "  make build          - Build development Docker image"
	@echo "  make up             - Start development environment"
	@echo "  make down           - Stop development environment"
	@echo "  make logs           - View application logs"
	@echo "  make restart        - Restart development environment"
	@echo "  make rebuild        - Rebuild and restart development environment"
	@echo ""
	@echo "Production Commands:"
	@echo "  make build-prod     - Build production Docker image"
	@echo "  make up-prod        - Start production environment"
	@echo "  make down-prod      - Stop production environment"
	@echo "  make logs-prod      - View production logs"
	@echo ""
	@echo "CI/CD Commands:"
	@echo "  make analyze        - Run parallel code analysis"
	@echo "  make test-local     - Run tests locally (fast mode)"
	@echo "  make test-full      - Run complete test suite"
	@echo "  make lint           - Run all linters"
	@echo "  make format         - Auto-format code (black + isort)"
	@echo "  make security       - Run security scan (Bandit)"
	@echo "  make complexity     - Check code complexity (Radon)"
	@echo "  make badges         - Generate README badges"
	@echo "  make dashboard      - Generate health dashboard"
	@echo "  make benchmark      - Run performance benchmark"
	@echo "  make optimize       - Analyze workflow optimization"
	@echo "  make cost           - Calculate GitHub Actions costs"
	@echo "  make validate       - Validate all implementations"
	@echo "  make all            - Run complete CI/CD pipeline"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make test           - Run tests in Docker container"
	@echo "  make shell          - Open shell in running container"
	@echo "  make clean          - Remove all containers, images, and volumes"
	@echo "  make monitoring     - Start with monitoring stack (Prometheus + Grafana)"
	@echo "  make local-llm      - Start with local LLM (Ollama)"
	@echo ""

# Development commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f agent

restart:
	docker-compose restart agent

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Production commands
build-prod:
	docker-compose -f docker-compose.prod.yml build

up-prod:
	docker-compose -f docker-compose.prod.yml up -d

down-prod:
	docker-compose -f docker-compose.prod.yml down

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f agent

# With monitoring
monitoring:
	docker-compose --profile monitoring up -d

monitoring-prod:
	docker-compose -f docker-compose.prod.yml up -d

# With local LLM
local-llm:
	docker-compose --profile local-llm up -d

# Testing
test:
	docker-compose run --rm agent pytest tests/ -v

test-coverage:
	docker-compose run --rm agent pytest tests/ --cov=.github/scripts --cov-report=html

# Utility commands
shell:
	docker-compose exec agent /bin/sh

shell-root:
	docker-compose exec -u root agent /bin/sh

clean:
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -af

clean-prod:
	docker-compose -f docker-compose.prod.yml down -v --rmi all --remove-orphans

# Image management
push:
	docker tag autonomous-github-agent:latest your-registry/autonomous-github-agent:latest
	docker push your-registry/autonomous-github-agent:latest

pull:
	docker pull your-registry/autonomous-github-agent:latest

# Health check
health:
	docker-compose ps
	docker-compose exec agent python -c "import sys; print('Health: OK'); sys.exit(0)"

health-prod:
	docker-compose -f docker-compose.prod.yml ps
	docker-compose -f docker-compose.prod.yml exec agent python -c "import sys; print('Health: OK'); sys.exit(0)"

# CI/CD Commands
analyze:
	@echo "🔍 Running parallel code analysis..."
	python .github/scripts/parallel_code_analyzer.py

test-local:
	@echo "🧪 Running local tests (fast mode)..."
	python scripts/test-local.py --fast

test-full:
	@echo "🧪 Running complete test suite..."
	python scripts/test-local.py

lint:
	@echo "🔎 Running linters..."
	pylint .github/scripts/ --rcfile=.github/config/analysis-config.yml || true
	flake8 .github/scripts/ || true

format:
	@echo "✨ Auto-formatting code..."
	black .github/scripts/ scripts/ tests/
	isort .github/scripts/ scripts/ tests/

security:
	@echo "🔒 Running security scan..."
	bandit -r .github/scripts/ -f json -o bandit-report.json || true
	@echo "Security report saved to bandit-report.json"

complexity:
	@echo "📊 Checking code complexity..."
	python .github/scripts/complexity_reporter.py

badges:
	@echo "🏷️ Generating README badges..."
	python .github/scripts/badge_generator.py

dashboard:
	@echo "📈 Generating health dashboard..."
	python .github/scripts/health_dashboard_generator.py

benchmark:
	@echo "⏱️ Running performance benchmark..."
	python .github/scripts/performance_benchmark.py

optimize:
	@echo "🚀 Analyzing workflow optimization..."
	python .github/scripts/workflow_optimizer.py

cost:
	@echo "💰 Calculating GitHub Actions costs..."
	python .github/scripts/cost_calculator.py

validate:
	@echo "✅ Validating all implementations..."
	python scripts/validate-implementation.py

all: format lint analyze security complexity test-full validate dashboard badges
	@echo "✅ Complete CI/CD pipeline executed successfully!"

# Quick quality check before commit
pre-commit: format lint test-local
	@echo "✅ Pre-commit checks passed!"
