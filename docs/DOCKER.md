# Docker Deployment Guide

This guide covers containerization and deployment of the Autonomous GitHub Agent using Docker.

## Quick Start

### Development Environment

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and start:**
   ```bash
   docker-compose up -d
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f agent
   ```

### Production Environment

1. **Prepare production configuration:**
   ```bash
   cp .env.production.example .env.production
   # Edit .env.production with your production values
   ```

2. **Build and deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Using the Makefile

The project includes a Makefile for common Docker operations:

```bash
# Development
make build          # Build development image
make up             # Start development environment
make down           # Stop development environment
make logs           # View logs
make restart        # Restart services

# Production
make build-prod     # Build production image
make up-prod        # Start production environment
make down-prod      # Stop production environment

# Testing
make test           # Run tests in container
make test-coverage  # Run tests with coverage

# Utilities
make shell          # Open shell in container
make clean          # Clean up everything
make health         # Check health status
```

## Docker Files Overview

### Dockerfile
Optimized multi-stage Dockerfile with:
- **Build caching** for faster rebuilds
- **Security hardening** (non-root user, minimal base image)
- **Layer optimization** for efficient builds
- **Pinned versions** for reproducibility

### docker-compose.yml (Development)
Development environment featuring:
- Hot-reload with volume mounts
- Resource limits for development
- Optional monitoring stack (Prometheus + Grafana)
- Optional local LLM (Ollama)

To start with monitoring:
```bash
docker-compose --profile monitoring up -d
```

To start with local LLM:
```bash
docker-compose --profile local-llm up -d
```

### docker-compose.prod.yml (Production)
Production-ready configuration with:
- Strict resource limits
- Security hardening
- Health checks
- Log rotation
- Read-only filesystem
- Automatic restarts

### .dockerignore
Excludes unnecessary files from build context to:
- Reduce image size
- Speed up builds
- Prevent sensitive data leaks

## Configuration

### Environment Variables

Key environment variables:

```bash
# GitHub
GITHUB_TOKEN=your_token
GITHUB_REPOSITORY_OWNER=your-username
GITHUB_REPOSITORY_NAME=your-repo

# AI/LLM
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
AGENT_MODEL=gpt-4

# Application
LOG_LEVEL=INFO
DEBUG=false
```

### Volumes

Development volumes:
- `./.github:/app/.github:ro` - Source code (read-only)
- `agent-data:/app/data` - Persistent data
- `agent-logs:/app/logs` - Application logs

Production volumes:
- `agent-data:/app/data` - Persistent data (bind mount)
- `agent-logs:/app/logs` - Application logs (bind mount)

## Monitoring

### Prometheus
Access metrics at: http://localhost:9090

### Grafana
Access dashboards at: http://localhost:3000
- Default credentials: admin/admin (change in production)

## Resource Management

### Development Limits
- CPU: 2 cores max, 0.5 reserved
- Memory: 2GB max, 512MB reserved

### Production Limits
- CPU: 4 cores max, 1 core reserved
- Memory: 4GB max, 1GB reserved

Adjust in `docker-compose.yml` or `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 1G
```

## Security Best Practices

1. **Non-root user**: Application runs as user `agent` (UID 1000)
2. **Read-only filesystem**: Production containers use read-only root filesystem
3. **No new privileges**: Security option prevents privilege escalation
4. **Secrets management**: Use Docker secrets or environment files (never commit to git)
5. **Network isolation**: Services communicate on isolated bridge network
6. **Minimal base image**: Using `python:3.11.7-slim` for smaller attack surface

## Troubleshooting

### View logs
```bash
docker-compose logs -f agent
```

### Check container health
```bash
docker-compose ps
make health
```

### Access container shell
```bash
make shell
# or with root privileges
make shell-root
```

### Rebuild from scratch
```bash
make rebuild
```

### Clean everything
```bash
make clean
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t autonomous-github-agent:latest .
      
      - name: Run tests
        run: docker run --rm autonomous-github-agent:latest pytest tests/
      
      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker tag autonomous-github-agent:latest your-registry/autonomous-github-agent:${{ github.sha }}
          docker push your-registry/autonomous-github-agent:${{ github.sha }}
```

## Production Deployment

### Using Docker Swarm

```bash
docker stack deploy -c docker-compose.prod.yml agent-stack
```

### Using Kubernetes

Convert compose file to Kubernetes manifests:

```bash
kompose convert -f docker-compose.prod.yml
kubectl apply -f .
```

## Backup and Recovery

### Backup volumes
```bash
docker run --rm -v agent-data:/data -v $(pwd):/backup alpine tar czf /backup/agent-data-backup.tar.gz -C /data .
```

### Restore volumes
```bash
docker run --rm -v agent-data:/data -v $(pwd):/backup alpine tar xzf /backup/agent-data-backup.tar.gz -C /data
```

## Performance Tuning

### Build performance
Enable BuildKit for faster builds:
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Runtime performance
- Use `--memory` and `--cpus` flags to limit resources
- Monitor with `docker stats`
- Use health checks for automatic recovery

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
