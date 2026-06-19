# Multi-stage Dockerfile for Autonomous GitHub Agent
# Optimized for build speed, caching, security, and size

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies in a single layer with cache cleanup
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching (least changing)
COPY requirements.txt .

# Install Python dependencies with pip cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-warn-script-location --no-cache-dir \
    -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Add security labels
LABEL maintainer="Autonomous GitHub Agent" \
      org.opencontainers.image.description="Autonomous GitHub Agent - AI-powered repository management" \
      org.opencontainers.image.source="https://github.com/autonomous-github-agent"

WORKDIR /app

# Create non-root user with specific UID/GID for security
RUN groupadd -r -g 1000 agent && \
    useradd -r -u 1000 -g agent -m -s /sbin/nologin agent && \
    chown -R agent:agent /app

# Copy Python packages from builder stage
COPY --from=builder --chown=agent:agent /root/.local /home/agent/.local

# Copy configuration files (change less frequently)
COPY --chown=agent:agent .github/config/ ./.github/config/
COPY --chown=agent:agent monitoring/ ./monitoring/
COPY --chown=agent:agent *.yml *.yaml ./

# Copy scripts (change moderately)
COPY --chown=agent:agent .github/scripts/ ./.github/scripts/
COPY --chown=agent:agent scripts/ ./scripts/

# Copy application code last (changes most frequently)
COPY --chown=agent:agent *.py ./

# Set environment variables
ENV PATH=/home/agent/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ANALYSIS_CACHE=true \
    USE_ORJSON=true \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Switch to non-root user
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", ".github/scripts/ai_agent_main.py", "--context", "context.json"]
